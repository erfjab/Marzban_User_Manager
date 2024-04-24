#!/bin/bash

check_and_install_python3() {
    if ! command -v python3 &>/dev/null; then
        echo -e "\e[34mInstalling Python3...\e[0m"
        apt update
        apt install -y python3 || { echo -e "\e[31mFailed to install Python3. Exiting...\e[0m"; exit 1; }
    else
        echo -e "\e[34mPython3 is already installed.\e[0m"
    fi
}

check_and_install_pip() {
    if ! command -v pip &>/dev/null; then
        echo -e "\e[34mInstalling pip...\e[0m"
        apt install -y python3-pip || { echo -e "\e[31mFailed to install pip. Exiting...\e[0m"; exit 1; }
    else
        echo -e "\e[34mPip is already installed.\e[0m"
    fi
}

clone_repository() {
    echo -e "\e[34mCloning Marzban_User_Manager repository...\e[0m"
    if [ -d "Marzban_User_Manager" ]; then
        echo -e "\e[34mRemoving existing Marzban_User_Manager directory...\e[0m"
        rm -rf Marzban_User_Manager || { echo -e "\e[31mFailed to remove existing directory. Exiting...\e[0m"; exit 1; }
    fi
    git clone https://github.com/M03ED/Marzban_User_Manager || { echo -e "\e[31mFailed to clone the repository. Exiting...\e[0m"; exit 1; }
}

install_dependencies() {
    cd Marzban_User_Manager || { echo -e "\e[31mFailed to change directory. Exiting...\e[0m"; exit 1; }
    echo -e "\e[34mInstalling Python dependencies...\e[0m"
    python3 -m pip install -r requirements.txt || { echo -e "\e[31mFailed to install dependencies. Exiting...\e[0m"; exit 1; }
}

run_main_script() {
    echo -e "\e[34mRunning the main script...\e[0m"
    python3 main.py
}

clear
check_and_install_python3
check_and_install_pip
clone_repository
install_dependencies
run_main_script
