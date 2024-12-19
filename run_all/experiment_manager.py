import os

class ExperimentManager:
    def __init__(self, base_dir="experiments"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)
        self.exp_dir = self.create_new_experiment_folder()

    def create_new_experiment_folder(self):
        """Create a new folder with incremental naming (e.g., exp_1, exp_2, ...)."""
        existing_dirs = [d for d in os.listdir(self.base_dir) if d.startswith("exp_") and os.path.isdir(os.path.join(self.base_dir, d))]
        exp_numbers = [int(d.split('_')[1]) for d in existing_dirs if d.split('_')[1].isdigit()]
        next_exp_number = max(exp_numbers, default=0) + 1
        new_exp_dir = os.path.join(self.base_dir, f"exp_{next_exp_number}")
        os.makedirs(new_exp_dir, exist_ok=True)
        return new_exp_dir

    def get_exp_folder(self):
        return self.exp_dir