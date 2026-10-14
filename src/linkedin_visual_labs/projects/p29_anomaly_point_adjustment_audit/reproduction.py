"""Standalone export assembly and isolated Project 9 reproduction primitives."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterable, Set
from dataclasses import dataclass
from email.parser import BytesParser
from email.policy import default
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ExportReceipt:
    export_root: Path
    manifest_path: Path
    manifest_sha256: str
    file_count: int
    total_size: int


@dataclass(frozen=True, slots=True)
class PublicationInputBundleReceipt:
    """Hash-verified frozen inputs for an installed publication build."""

    bundle_root: Path
    manifest_path: Path
    manifest_sha256: str
    file_count: int


@dataclass(frozen=True, slots=True)
class ReproductionReceipt:
    venv_python: Path
    export_root: Path
    import_probe: dict[str, object]
    commands: tuple[dict[str, object], ...]


@dataclass(frozen=True, slots=True)
class WheelRecord:
    """A locally available wheel and the metadata needed to lock it."""

    filename: str
    distribution: str
    version: str
    tags: tuple[str, ...]
    size_bytes: int
    sha256: str
    source_class: str
    requires_dist: tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_publication_input_bundle(
    repository_root: Path, destination_root: Path
) -> PublicationInputBundleReceipt:
    """Copy and hash-verify the minimal frozen inputs for installed publication."""
    source_root = repository_root.resolve()
    bundle_root = (destination_root.resolve() / "publication_inputs").resolve()
    if not bundle_root.is_relative_to(destination_root.resolve()):
        raise ValueError("publication input bundle escapes destination root")
    entries: list[dict[str, object]] = []
    sources = (
        (
            "release_data",
            "outputs/p29_anomaly_point_adjustment_audit/data/release_data.json",
            "data/release_data.json",
            "frozen publication science input",
        ),
        (
            "claim_register",
            "outputs/p29_anomaly_point_adjustment_audit/manifests/claim_register.json",
            "manifests/claim_register.json",
            "approved publication claims input",
        ),
        (
            "source_provenance",
            "reference/project9/source_provenance.json",
            "reference/source_provenance.json",
            "frozen publication provenance input",
        ),
    )
    for logical_name, source_relative, destination_relative, reason in sources:
        source = source_root / source_relative
        target = bundle_root / destination_relative
        if not source.is_file():
            raise FileNotFoundError(f"missing canonical publication input {logical_name}: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        source_hash, target_hash = _sha256(source), _sha256(target)
        if source_hash != target_hash:
            raise ValueError(f"publication input hash mismatch: {logical_name}")
        entries.append(
            {
                "logical_name": logical_name,
                "canonical_relative_path": source_relative,
                "clean_relative_path": destination_relative,
                "size_bytes": target.stat().st_size,
                "canonical_sha256": source_hash,
                "clean_sha256": target_hash,
                "equality": "PASS",
                "reason_included": reason,
            }
        )
    manifest_path = bundle_root / "publication_input_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {"schema_version": "p29-publication-inputs-v1", "entries": entries},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return PublicationInputBundleReceipt(
        bundle_root=bundle_root,
        manifest_path=manifest_path,
        manifest_sha256=_sha256(manifest_path),
        file_count=len(entries),
    )


def inspect_wheel(path: Path, source_class: str) -> WheelRecord:
    """Read filename tags and embedded distribution metadata from one wheel."""
    import zipfile

    from packaging.utils import parse_wheel_filename

    name, version, _build, tags = parse_wheel_filename(path.name)
    with zipfile.ZipFile(path) as archive:
        metadata_name = next(
            member for member in archive.namelist() if member.endswith(".dist-info/METADATA")
        )
        metadata = BytesParser(policy=default).parsebytes(archive.read(metadata_name))
    return WheelRecord(
        filename=path.name,
        distribution=str(metadata["Name"] or name),
        version=str(metadata["Version"] or version),
        tags=tuple(sorted(str(tag) for tag in tags)),
        size_bytes=path.stat().st_size,
        sha256=_sha256(path),
        source_class=source_class,
        requires_dist=tuple(metadata.get_all("Requires-Dist", [])),
    )


def inspect_wheels(paths: Iterable[Path], source_class: str) -> tuple[WheelRecord, ...]:
    """Return deterministically ordered records for local wheel files."""
    return tuple(
        inspect_wheel(path, source_class) for path in sorted(paths, key=lambda item: item.name)
    )


def verify_wheel_compatibility(
    records: Iterable[WheelRecord], supported_tags: Iterable[str]
) -> None:
    """Reject a wheel when none of its tags apply to the selected interpreter."""
    supported = set(supported_tags)
    incompatible = [
        record.filename for record in records if not supported.intersection(record.tags)
    ]
    if incompatible:
        raise ValueError(f"incompatible wheels: {', '.join(sorted(incompatible))}")


def validate_dependency_closure(records: Iterable[WheelRecord]) -> None:
    """Ensure all unconditional wheel metadata requirements are locally represented."""
    from packaging.markers import default_environment
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name
    from packaging.version import Version

    available = {
        canonicalize_name(record.distribution): Version(record.version) for record in records
    }
    environment: dict[str, str | Set[str]] = {}
    for key, value in default_environment().items():
        if not isinstance(value, str):
            raise TypeError("wheel marker environment values must be strings")
        environment[key] = value
    missing: list[str] = []
    for record in records:
        for raw_requirement in record.requires_dist:
            requirement = Requirement(raw_requirement)
            if requirement.marker and not requirement.marker.evaluate(environment):
                continue
            name = canonicalize_name(requirement.name)
            version = available.get(name)
            if version is None or (requirement.specifier and version not in requirement.specifier):
                missing.append(f"{record.distribution}: {raw_requirement}")
    if missing:
        raise ValueError(f"unsatisfied wheel metadata requirements: {'; '.join(sorted(missing))}")


def write_wheelhouse_receipts(
    wheelhouse: Path,
    records: Iterable[WheelRecord],
    export_manifest_sha256: str,
    project_wheel_sha256: str,
    direct_pins: Iterable[str],
) -> tuple[Path, str, Path]:
    """Write sorted manifest and hash-locked requirements for an offline wheelhouse."""
    selected = tuple(sorted(records, key=lambda record: record.filename.lower()))
    manifest = {
        "schema_version": "p29-wheelhouse-v1",
        "target_python": "CPython 3.13",
        "target_platform": "Windows AMD64",
        "target_abi_policy": ["cp313", "abi3", "none"],
        "project9_export_manifest_sha256": export_manifest_sha256,
        "project9_wheel_sha256": project_wheel_sha256,
        "direct_dependency_pins": list(direct_pins),
        "acquisition_method": "binary-only pip download followed by offline installation",
        "wheels": [
            {
                "filename": record.filename,
                "distribution": record.distribution,
                "version": record.version,
                "tags": list(record.tags),
                "size_bytes": record.size_bytes,
                "sha256": record.sha256,
                "source_class": record.source_class,
                "requires_dist": list(record.requires_dist),
            }
            for record in selected
        ],
    }
    manifest_path = wheelhouse / "wheelhouse_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    lock_path = wheelhouse / "wheelhouse_requirements.lock"
    lock_path.write_text(
        "".join(
            f"{record.distribution}=={record.version} --hash=sha256:{record.sha256}\n"
            for record in selected
            if record.source_class != "PROJECT9_EXPORT_BUILD"
        ),
        encoding="utf-8",
    )
    return manifest_path, _sha256(manifest_path), lock_path


def _copy_file(
    source: Path, root: Path, destination: Path, entries: list[dict[str, object]]
) -> None:
    resolved_root, resolved_source, resolved_destination = (
        root.resolve(),
        source.resolve(),
        destination.resolve(),
    )
    if not resolved_source.is_relative_to(resolved_root) or not resolved_destination.is_relative_to(
        destination.parents[0].resolve()
    ):
        raise ValueError("export path containment failed")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    entries.append({"relative_path": destination.relative_to(destination.parents[0]).as_posix()})


def build_standalone_export(repository_root: Path, destination_root: Path) -> ExportReceipt:
    """Build a deterministic, Project-9-only installable export."""
    source_root = repository_root.resolve()
    export = destination_root.resolve() / "project9_anomaly_evaluation_export"
    export.mkdir(parents=True, exist_ok=True)
    for generated in (
        export / "build",
        export / "src" / "project9_anomaly_evaluation_export.egg-info",
    ):
        if generated.exists():
            if not generated.resolve().is_relative_to(export.resolve()):
                raise ValueError("generated export artifact containment failed")
            shutil.rmtree(generated)
    entries: list[dict[str, object]] = []
    include_roots = (
        "src/linkedin_visual_labs/projects/p29_anomaly_point_adjustment_audit",
        "configs/p29_anomaly_point_adjustment_audit.yaml",
        "reference/project9",
        "docs/projects/p29_anomaly_point_adjustment_audit",
        "tests/projects/p29_anomaly_point_adjustment_audit",
        "outputs/p29_anomaly_point_adjustment_audit/data",
        "outputs/p29_anomaly_point_adjustment_audit/manifests",
        "outputs/p29_anomaly_point_adjustment_audit/figures",
        "outputs/p29_anomaly_point_adjustment_audit/dashboard",
        "outputs/p29_anomaly_point_adjustment_audit/video",
        "outputs/p29_anomaly_point_adjustment_audit/publication",
        "outputs/p29_anomaly_point_adjustment_audit/publication_metadata",
    )
    for relative in include_roots:
        item = source_root / relative
        files = (
            (item,)
            if item.is_file()
            else sorted(path for path in item.rglob("*") if path.is_file())
        )
        for source in files:
            if (
                any(part in {"__pycache__", ".pytest_cache", ".venv"} for part in source.parts)
                or source.suffix == ".pyc"
            ):
                continue
            target = export / source.relative_to(source_root)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            entries.append(
                {
                    "relative_path": target.relative_to(export).as_posix(),
                    "size_bytes": target.stat().st_size,
                    "sha256": _sha256(target),
                    "source_relative_path": source.relative_to(source_root).as_posix(),
                    "artifact_class": "project9",
                    "reason_included": "Project 9 standalone reproduction",
                    "reproduction_role": "input_or_tooling",
                }
            )
    resource_sources = (
        (
            "configs/p29_anomaly_point_adjustment_audit.yaml",
            "p29_anomaly_point_adjustment_audit.yaml",
        ),
        ("reference/project9/semantic_fixtures.json", "semantic_fixtures.json"),
        ("reference/project9/experiment_design.json", "experiment_design.json"),
        ("docs/projects/p29_anomaly_point_adjustment_audit/STATE.json", "STATE.json"),
        (
            "docs/projects/p29_anomaly_point_adjustment_audit/PROJECT_CONTRACT.md",
            "PROJECT_CONTRACT.md",
        ),
        (
            "docs/projects/p29_anomaly_point_adjustment_audit/EXPERIMENT_PROTOCOL.md",
            "EXPERIMENT_PROTOCOL.md",
        ),
    )
    resource_root = (
        export / "src/linkedin_visual_labs/projects/p29_anomaly_point_adjustment_audit/resources"
    )
    resource_root.mkdir(parents=True, exist_ok=True)
    for source_relative, resource_name in resource_sources:
        canonical = source_root / source_relative
        packaged = resource_root / resource_name
        shutil.copy2(canonical, packaged)
        if _sha256(canonical) != _sha256(packaged):
            raise ValueError("packaged runtime resource hash does not match canonical source")
        entries.append(
            {
                "relative_path": packaged.relative_to(export).as_posix(),
                "size_bytes": packaged.stat().st_size,
                "sha256": _sha256(packaged),
                "source_relative_path": source_relative,
                "artifact_class": "PACKAGE_RESOURCE",
                "reason_included": "Installed Project 9 runtime resource",
                "reproduction_role": "package_resource",
            }
        )
    (export / "src/linkedin_visual_labs/__init__.py").parent.mkdir(parents=True, exist_ok=True)
    (export / "src/linkedin_visual_labs/__init__.py").write_text(
        '"""Project 9 standalone package."""\n', encoding="utf-8"
    )
    (export / "src/linkedin_visual_labs/projects/__init__.py").parent.mkdir(
        parents=True, exist_ok=True
    )
    (export / "src/linkedin_visual_labs/projects/__init__.py").write_text(
        '"""Project namespaces."""\n', encoding="utf-8"
    )
    (export / "pyproject.toml").write_text(
        '[build-system]\nrequires=["setuptools>=75"]\nbuild-backend="setuptools.build_meta"\n[project]\nname="project9-anomaly-evaluation-export"\nversion="0.1.0"\nrequires-python=">=3.13,<3.14"\ndependencies=["numpy>=2.1","PyYAML>=6.0","matplotlib>=3.9","imageio>=2.36","imageio-ffmpeg>=0.5"]\n[project.optional-dependencies]\nproject9-publication=["python-docx>=1.1","reportlab>=4.2","pypdf>=5.0","PyMuPDF>=1.24"]\n[tool.setuptools]\npackage-dir={""="src"}\n[tool.setuptools.packages.find]\nwhere=["src"]\n[tool.setuptools.package-data]\n"linkedin_visual_labs.projects.p29_anomaly_point_adjustment_audit"=["resources/*.yaml","resources/*.json","resources/*.md"]\n',
        encoding="utf-8",
    )
    entries.sort(key=lambda entry: str(entry["relative_path"]))
    manifest = {
        "schema_version": "p29-export-v1",
        "entries": entries,
        "excluded": [".git", ".venv", ".pytest_cache", "__pycache__", "Projects 1-8"],
    }
    manifest_path = export / "export_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    total_size = 0
    for entry in entries:
        size = entry["size_bytes"]
        if not isinstance(size, int):
            raise TypeError("export manifest size must be an integer")
        total_size += size
    return ExportReceipt(
        export,
        manifest_path,
        _sha256(manifest_path),
        len(entries),
        total_size,
    )


def run_clean_reproduction(export_root: Path, work_root: Path) -> ReproductionReceipt:
    """Create a fresh venv, install the export, and prove imports avoid the developer checkout."""
    venv = work_root.resolve() / "venv"
    temp = work_root.resolve() / "temp"
    temp.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    environment["PYTHONNOUSERSITE"] = "1"
    environment["TEMP"] = str(temp)
    environment["TMP"] = str(temp)
    try:
        subprocess.run([sys.executable, "-m", "venv", str(venv)], env=environment, check=True)
    except subprocess.CalledProcessError:
        subprocess.run(
            [sys.executable, "-m", "venv", "--without-pip", str(venv)],
            env=environment,
            check=True,
        )
        subprocess.run(
            [str(venv / "Scripts" / "python.exe"), "-m", "ensurepip", "--upgrade"],
            cwd=work_root,
            env=environment,
            check=True,
        )
    python = venv / "Scripts" / "python.exe"
    subprocess.run(
        [str(python), "-m", "pip", "install", ".[project9-publication]"],
        cwd=export_root,
        env=environment,
        check=True,
    )
    probe = "import json,sys,linkedin_visual_labs; import docx,reportlab,pypdf,fitz; print(json.dumps({'sys_path':sys.path,'package':linkedin_visual_labs.__file__,'docx':docx.__file__,'reportlab':reportlab.__file__,'pypdf':pypdf.__file__,'fitz':fitz.__file__}))"  # noqa: E501
    result = subprocess.run(
        [str(python), "-c", probe],
        cwd=work_root,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    values = json.loads(result.stdout)
    if not str(values["package"]).startswith(str(venv)):
        raise RuntimeError("developer-checkout leakage detected")
    return ReproductionReceipt(python, export_root, values, ())
