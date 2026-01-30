import os

ROOT = "_DEMO_PROJECT"

STRUCTURE = {
    "01_Planning": {
        "Requirements.md": "# System Requirements\n\n1. User Authentication\n2. Data Visualization\n3. High Performance",
        "Budget.xlsx": None,
        "Meeting_Logs": {
            "2024-01-10.txt": "Kickoff meeting notes...",
            "2024-01-17.txt": "Design review notes...",
            "2024-01-24.txt": "Sprint planning notes..."
        }
    },
    "02_Design": {
        "UI_Assets": {
            "Logo_Variants": {
               "logo_white.png": None,
               "logo_black.png": None,
               "logo_primary.svg": None
            },
            "Mockups": {
                "Dashboard_v1.png": None,
                "Settings_Page.png": None,
                "Login_Screen.png": None
            }
        },
        "StyleGuide.pdf": None,
    },
    "03_Development": {
        "backend": {
            "api": {
                "v1": {
                    "users.py": "def get_users():\n    return []",
                    "auth.py": "def login():\n    pass",
                    "products.py": "def list_products():\n    pass"
                },
                "models.py": "class User:\n    pass\n\nclass Product:\n    pass",
                "utils.py": "def helper():\n    pass"
            },
            "db": {
                 "migrations": {
                     "001_initial.sql": "CREATE TABLE users...",
                     "002_add_products.sql": "CREATE TABLE products..."
                 },
                 "seeds.json": "{}"
            },
            "config.yaml": "database: postgresql\nhost: localhost",
        },
        "frontend": {
            "src": {
                "components": {
                    "common": {
                        "Button.jsx": "export const Button = () => <button>Click</button>",
                        "Header.jsx": "export const Header = () => <header>Logo</header>",
                        "Footer.jsx": "export const Footer = () => <footer>Copyright</footer>"
                    },
                    "forms": {
                        "LoginForm.jsx": "",
                        "SignupForm.jsx": ""
                    }
                },
                "pages": {
                    "Home.js": "import React from 'react';",
                    "Dashboard.js": "",
                    "Profile.js": ""
                },
                "App.js": "import React from 'react';\nimport { Home } from './pages/Home';",
            },
            "public": {
                "index.html": "<html><body><div id='root'></div></body></html>",
                "favicon.ico": None
            },
            "package.json": "{\n  \"name\": \"demo-app\",\n  \"version\": \"1.0.0\"\n}",
        },
        "scripts": {
            "deploy.sh": "#!/bin/bash\necho 'Deploying...'",
            "test.py": "import unittest\n\nclass TestApp(unittest.TestCase):\n    pass",
        }
    },
    "04_Marketing": {
        "Campaigns": {
            "Q1_Launch": {
                "Social_Media": {
                    "Twitter_Posts.txt": "Tweet 1: Hello World!",
                    "Instagram_Stories": {},
                    "LinkedIn_Drafts.docx": None
                },
                "Emails": {
                    "Newsletter_Jan.html": "<h1>Happy New Year</h1>"
                },
            },
            "Q2_Updates": {},
        },
        "Resources": {
            "Images": {
                "Banner_Large.jpg": None,
                "Banner_Small.jpg": None
            }
        }
    },
    "99_Archive": {
        "Old_Projects": {
            "2020_Alpha": {},
            "2021_Beta": {},
            "2022_Legacy": {
                 "Deeply_Nested": {
                     "Level_1": {
                         "Level_2": {
                             "Level_3": {
                                 "Level_4": {
                                     "Level_5": {
                                         "Secret_Code.js": "console.log('You found me!');"
                                     }
                                 }
                             }
                         }
                     }
                 }
            },
        }
    }
}

def create_structure(base_path, structure):
    if not os.path.exists(base_path):
        os.makedirs(base_path)
    
    for name, content in structure.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            create_structure(path, content)
        else:
            # File
            with open(path, 'w', encoding='utf-8') as f:
                if content:
                    f.write(content)
                else:
                    pass # Empty file

if __name__ == "__main__":
    create_structure(ROOT, STRUCTURE)
    print(f"Created demo structure at {os.path.abspath(ROOT)}")
