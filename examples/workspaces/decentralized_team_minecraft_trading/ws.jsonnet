//local players = ["Bob", "Thomas", "Jessica", "Sarah"];
local players = ["Bob", "Thomas"];
local admin_agent_name = "Admin";
local organizer_agent_name = "Organizer";
local initial_inventory = {
    "Bob": {
        "stone": 100,
        "diamond": 50,
        "gold_ingot": 20,
        "coin": 1000
    },
    "Thomas": {
        "wood": 32,
        "coin": 3000
    },
//    "Jessica": {
//        "stone": 10,
//        "fish": 10,
//        "coin": 2000
//    },
//    "Sarah": {
//        "obsidian": 1,
//        "coin": 0
//    }
};

local goals = {
    "Bob": "Your goal is to get as many coins as possible.",
    "Thomas": "Your goal is to get at least 10 diamond and keep at least 1000 coins.",
//    "Jessica": "Your goal is to be the one with most amount of stone in the game.",
//    "Sarah": "Your goal is to collect at least 10 diamond."
};

local workspace = {
    title: "Decentralized Minecraft Trading",
    description: "Simulating multiple minecraft players trading items to achieve individual goals.",
    default_channel: organizer_agent_name,
    start_messages: [
        {
            source: organizer_agent_name,
            destination: "human",
            content: "Type 'start game' to start the trading competition."
        }
    ],
    agents: [
        {
            type: 'MinecraftOrganizer',
            name: organizer_agent_name,
            admin_name: admin_agent_name,
            players: players
        },
        {
            type: 'MinecraftTradingAdmin',
            name: admin_agent_name,
            organizer_name: organizer_agent_name,
            players: players,
            initial_inventory: initial_inventory
        },
        {
            type: 'MinecraftPlayer',
            name: 'Bob',
            players: players,
            organizer_name: organizer_agent_name,
            admin_name: admin_agent_name,
            instruction: goals['Bob']
        },
        {
            type: 'MinecraftPlayer',
            name: 'Thomas',
            players: players,
            organizer_name: organizer_agent_name,
            admin_name: admin_agent_name,
            instruction: goals['Thomas']
        },
//        {
//            type: 'MinecraftPlayer',
//            name: 'Jessica',
//            players: players,
//            organizer_name: organizer_agent_name,
//            admin_name: admin_agent_name,
//            instruction: goals['Jessica']
//        },
//        {
//            type: 'MinecraftPlayer',
//            name: 'Sarah',
//            players: players,
//            organizer_name: organizer_agent_name,
//            admin_name: admin_agent_name,
//            instruction: goals['Sarah']
//        }
    ]
};

workspace