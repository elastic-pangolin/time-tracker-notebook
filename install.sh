if command -v python3 &> /dev/null; then
    python3 -m venv .venv
elif command -v python &> /dev/null; then
    python -m venv .venv
else
    echo "Python not installed. Please install Python and then rerun this script."
    exit 1
fi
source .venv/bin/activate && \
pip install --upgrade pip && \
pip install . && \
pip freeze # show installed packages
deactivate
