# espn-fantasy-utils

Once you've been granted access to AWS, please download the `creds.json` file from the s3 path `s3://espn-fantasy/creds/creds.json` and place it in your project root. This should enable you to interact with AWS and Oracle as needed.

## Repo Installation
Windows
```
# Install pyenv-win to user directory
Invoke-WebRequest -Uri https://pyenv.win/install.ps1 -OutFile install-pyenv.ps1
& ".\install-pyenv.ps1"

# Temporarily update PATH for this session only 
$env:Path = "$env:USERPROFILE\.pyenv\pyenv-win\bin;$env:USERPROFILE\.pyenv\pyenv-win\shims;$env:Path"

# Install and set Python 3.11.9
pyenv install 3.11.9
pyenv local 3.11.9

# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install your package
pip install .

# (Optional) For development use:
# pip install -e .
```

MacOS
```
# Install pyenv (macOS with Homebrew)
brew update
brew install pyenv

# OR: Install pyenv (Ubuntu / WSL)
curl https://pyenv.run | bash

# Add to ~/.bashrc or ~/.zshrc:
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv virtualenv-init -)"
exec "$SHELL"

# Install and set Python version
pyenv install 3.11.9
pyenv local 3.11.9

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install the package
pip install .

# (Optional) For development use:
# pip install -e .
```
