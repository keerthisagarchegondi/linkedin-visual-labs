"""The optional extra preserves the existing Zombie public DL API."""

from linkedin_visual_labs.projects import p04_zombie_escape as zombie
from linkedin_visual_labs.projects.p04_zombie_escape.dl_model import ZombieRiskCNN
from linkedin_visual_labs.projects.p04_zombie_escape.dl_pipeline import run_dl_pipeline
from linkedin_visual_labs.projects.p04_zombie_escape.dl_tensors import city_to_tensor


def test_lazy_public_dl_exports_preserve_implementations() -> None:
    assert zombie.ZombieRiskCNN is ZombieRiskCNN
    assert zombie.run_dl_pipeline is run_dl_pipeline
    assert zombie.city_to_tensor is city_to_tensor
