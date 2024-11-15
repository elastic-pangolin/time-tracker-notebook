SETTING UP OR CREATING A NOTEBOOK

If not already done: Install jupyter notebook (https://jupyter.org/install)

Create a folder (or clone from git) with a .ipynb (notebook) file and a pyproject.toml

Run the install.sh script from this new folder to create a virtual environment

Create a kernel using this environment by executing inside the folder:

> source .venv/bin/activate
> python -m ipykernel install --user --name {new-kernel-name}
> jupyter kernelspec list

Start jupyter service with

> jupyter notebook
