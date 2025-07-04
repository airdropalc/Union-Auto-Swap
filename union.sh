#!/bin/bash
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

BOT_DIR="Union_Bot"
PYTHON_SCRIPT_NAME="union.py"
SCREEN_SESSION_NAME="UnionBot"

initial_setup() {
    echo -e "${CYAN}➤ Starting initial setup for the Union Bot...${NC}"
    if [ ! -d "$BOT_DIR" ]; then
        echo -e "${CYAN}Creating bot directory: $BOT_DIR${NC}"
        mkdir "$BOT_DIR"
    else
        echo -e "${YELLOW}Directory '$BOT_DIR' already exists. Skipping creation.${NC}"
    fi

    echo -e "${CYAN}Downloading required files from GitHub...${NC}"
    (cd "$BOT_DIR" && wget -q --show-progress -O "$PYTHON_SCRIPT_NAME" "https://raw.githubusercontent.com/airdropalc/Union-Auto-Swap/refs/heads/main/union.py")
    (cd "$BOT_DIR" && wget -q --show-progress -O "requirements.txt" "https://raw.githubusercontent.com/airdropalc/Union-Auto-Swap/refs/heads/main/requirements.txt")
    echo -e "${GREEN}✓ Files downloaded successfully.${NC}"
    echo -e "${CYAN}➤ Installing required Python packages using pip...${NC}"
    pip install -r "$BOT_DIR/requirements.txt" --break-system-packages
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Dependencies installed successfully.${NC}"
    else
        echo -e "${RED}✗ Failed to install dependencies. Please check your pip and internet connection.${NC}"
        read -n 1 -s -r -p "Press any key to return to the menu..."
        return 1
    fi

    echo ""
    echo -e "${GREEN}✅ Initial setup completed! Please configure your accounts and proxy next.${NC}"
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

configure_accounts() {
    local accounts_file="$BOT_DIR/accounts.json"
    echo -e "${CYAN}➤ Account Configuration (accounts.json)${NC}"
    echo -e "${YELLOW}You will now be prompted to enter your account details.${NC}"
    echo -e "${YELLOW}You can add multiple accounts. Let's start with the first one.${NC}"
    echo "[" > "$accounts_file"
    
    local first_entry=true
    while true; do
        echo ""
        read -p "Enter EVM Private Key: " private_key
        read -p "Enter Xion Address: " xion_address
        read -p "Enter Babylon Address: " babylon_address

        if [ "$first_entry" = true ]; then
            first_entry=false
        else
            echo "," >> "$accounts_file"
        fi

        cat >> "$accounts_file" << EOL
    {
        "PrivateKey": "${private_key}",
        "XionAddress": "${xion_address}",
        "BabylonAddress": "${babylon_address}"
    }
EOL

        read -p "Do you want to add another account? [y/N]: " more
        if [[ ! "$more" =~ ^[Yy]$ ]]; then
            break
        fi
    done

    echo "]" >> "$accounts_file"
    echo -e "${GREEN}✓ Configuration saved to $accounts_file successfully.${NC}"
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

configure_proxy() {
    echo -e "${CYAN}➤ Proxy Configuration (proxy.txt)${NC}"
    echo -e "${YELLOW}Enter your proxies one by one. Press ENTER on an empty line to finish.${NC}"
    echo -e "${YELLOW}Format: http://username:password@host:port OR ip:port${NC}"

    > "$BOT_DIR/proxy.txt" 
    local count=0
    while true; do
        read -p "Enter proxy: " proxy_line
        if [ -z "$proxy_line" ]; then
            break
        fi
        echo "$proxy_line" >> "$BOT_DIR/proxy.txt"
        count=$((count + 1))
    done

    if [ "$count" -gt 0 ]; then
        echo -e "${GREEN}✓ Saved $count proxies to $BOT_DIR/proxy.txt successfully.${NC}"
    else
        echo -e "${YELLOW}⚠ No proxies were entered. The file is empty.${NC}"
    fi
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

run_bot() {
    if [ ! -f "$BOT_DIR/accounts.json" ]; then
        echo -e "${RED}✗ Configuration file (accounts.json) not found!${NC}"
        echo -e "${YELLOW}Please configure your accounts first (Option 2).${NC}"
    else
        echo -e "${CYAN}➤ Starting the bot in a background 'screen' session named '${SCREEN_SESSION_NAME}'...${NC}"
        (cd "$BOT_DIR" && screen -dmS "$SCREEN_SESSION_NAME" python3 "$PYTHON_SCRIPT_NAME")
        echo -e "${GREEN}✓ Bot has been started.${NC}"
        echo -e "${YELLOW}IMPORTANT: To view the bot's output, use Option 5 (Check Bot Status).${NC}"
        echo -e "${YELLOW}To detach from the session window after checking, press: ${CYAN}CTRL+A${YELLOW} then ${CYAN}D${NC}"
    fi
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

check_status() {
    echo -e "${CYAN}➤ Attaching to screen session '${SCREEN_SESSION_NAME}'...${NC}"
    echo -e "${YELLOW}To detach and return to the terminal, press: ${CYAN}CTRL+A${YELLOW} then ${CYAN}D${NC}"
    sleep 2
    screen -r "$SCREEN_SESSION_NAME"
    echo -e "\n${GREEN}Returned from screen session.${NC}"
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

stop_bot() {
    echo -e "${CYAN}➤ Attempting to stop the bot...${NC}"
    if screen -list | grep -q "$SCREEN_SESSION_NAME"; then
        screen -X -S "$SCREEN_SESSION_NAME" quit
        echo -e "${GREEN}✓ Bot session '${SCREEN_SESSION_NAME}' has been stopped.${NC}"
    else
        echo -e "${YELLOW}⚠ Bot session '${SCREEN_SESSION_NAME}' is not currently running.${NC}"
    fi
    echo ""
    read -n 1 -s -r -p "Press any key to return to the menu..."
}

while true; do
    clear
    echo -e "${CYAN}===============================================${NC}"
    echo -e "${CYAN}        UNION AUTO SWAP BY AIRDROP ALC         ${NC}"
    echo -e "${CYAN}===============================================${NC}"
    echo -e "Please choose an option:"
    echo -e "1. ${GREEN}Initial Setup${NC} (Download files & Install Dependencies)"
    echo -e "2. ${GREEN}Configure Accounts${NC} (Create accounts.json)"
    echo -e "3. ${GREEN}Configure Proxy${NC} (Create proxy.txt)"
    echo -e "4. ${GREEN}Run Bot${NC} (Starts the swapping process)"
    echo -e "5. ${YELLOW}Check Bot Status${NC} (View the bot's live output)"
    echo -e "6. ${RED}Stop Bot${NC}"
    echo -e "0. ${RED}Exit${NC}"
    echo -e "${CYAN}------------------------------------${NC}"
    read -p "Enter your choice [0-6]: " choice

    case $choice in
        1)
            initial_setup
            ;;
        2)
            configure_accounts
            ;;
        3)
            configure_proxy
            ;;
        4)
            run_bot
            ;;
        5)
            check_status
            ;;
        6)
            stop_bot
            ;;
        0)
            echo "Exiting. Goodbye!"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            sleep 2
            ;;
    esac
done
