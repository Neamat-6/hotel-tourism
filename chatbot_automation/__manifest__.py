{
    "name": "Chatbot UI Automation",
    "version": "1.0",
    "depends": ["web", "web_tour", "bus"],
    "data": [
        "security/ir.model.access.csv",
    ],
    "assets": {
        "web.assets_backend": [
            "chatbot_automation/static/src/css/highlight.css",
            "chatbot_automation/static/src/js/tour_launcher.js",
        ],
    },
    "installable": True,
}
