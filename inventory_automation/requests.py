"""
requests.py

Configuration for learning, anomaly detection,
threat intelligence, model updates, and output files.
"""


def request():
    """
    Return Defender learning configuration.
    """

    return {
        "learning_enabled": True,

        "learning_paths": [
            "process_behavior",
            "network_behavior",
            "file_activity",
            "registry_activity",
            "user_activity",
            "threat_patterns",
        ],

        "baseline_learning": {
            "enabled": True,
            "learning_days": 30,
        },

        "anomaly_detection": {
            "enabled": True,
            "sensitivity": 0.75,
        },

        "threat_intelligence": {
            "enabled": True,
            "feeds": [
                "cybertracker",
                "local_threat_db",
            ],
        },

        "model_updates": {
            "auto_update": True,
            "save_interval_minutes": 60,
        },

        "output_files": {
            "baseline": "data/baseline_model.json",
            "learning_log": "logs/learning.log",
            "threat_scores": "logs/threat_scores.json",
        },
    }