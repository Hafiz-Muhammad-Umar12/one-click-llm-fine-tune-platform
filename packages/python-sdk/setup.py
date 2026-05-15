from setuptools import setup, find_packages

setup(
    name="ai-platform-sdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "tqdm>=4.65.0",
        "click>=8.0.0"
    ],
    entry_points={
        "console_scripts": [
            "ai-platform=ai_platform.cli:main",
        ],
    },
    author="Gemini CLI",
    description="Python SDK for the One-Click AI Fine-Tuning Platform",
    python_requires=">=3.8",
)
