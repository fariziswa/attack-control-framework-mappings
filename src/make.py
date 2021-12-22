import json
import os
import subprocess
import sys


def find_file_with_suffix(suffix, folder):
    """find a file with the given suffix in the folder"""
    for f in os.listdir(folder):
        if f.endswith(suffix):
            return f
    return None


def main():
    """rebuild all control frameworks from the input data"""

    for attack_version in ["v8.2", "v9.0"]:
        for framework in ["nist800-53-r4", "nist800-53-r5"]:
            # move to the framework folder
            versioned_folder = f"ATT&CK-{attack_version}"
            framework_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frameworks",
                                            versioned_folder, framework)
            os.chdir(framework_folder)

            # read the framework config
            config_path = os.path.join("input", "config.json")
            if not os.path.exists(config_path):
                print("WARNING: framework has no config file, skipping")
                os.chdir(os.path.join("..", "..", "..", "src"))
                continue
            with open(config_path, "r") as f:
                config = json.load(f)

            # build the controls and mappings STIX
            subprocess.run([sys.executable, "parse.py"])
            os.chdir(os.path.join("..", "..", "..", "src"))

            # find the mapping and control files that were generated
            controls_file = find_file_with_suffix("-controls.json", os.path.join(framework_folder, "stix"))
            mappings_file = find_file_with_suffix("-mappings.json", os.path.join(framework_folder, "stix"))

            # run the utility scripts
            subprocess.run([
                sys.executable, "mappings_to_heatmaps.py",
                "-controls", os.path.join(framework_folder, "stix", controls_file),
                "-mappings", os.path.join(framework_folder, "stix", mappings_file),
                "-output", os.path.join(framework_folder, "layers"),
                "-domain", config["attack_domain"],
                "-version", config["attack_version"],
                "-framework", framework,
                "--clear",
                "--build-directory"
            ])
            subprocess.run([
                sys.executable, "substitute.py",
                "-controls", os.path.join(framework_folder, "stix", controls_file),
                "-mappings", os.path.join(framework_folder, "stix", mappings_file),
                "-output", os.path.join(framework_folder, "stix", f"{framework}-enterprise-attack.json"),
                "-domain", config["attack_domain"],
                "-version", config["attack_version"]
            ])
            subprocess.run([
                sys.executable, "list_mappings.py",
                "-controls", os.path.join(framework_folder, "stix", controls_file),
                "-mappings", os.path.join(framework_folder, "stix", mappings_file),
                "-output", os.path.join(framework_folder, f"{framework}-mappings.xlsx"),
                "-domain", config["attack_domain"],
                "-version", config["attack_version"]
            ])


if __name__ == "__main__":
    main()