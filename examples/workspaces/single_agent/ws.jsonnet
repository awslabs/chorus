local workspace = {
    title: "Testing Workspace",
    description: "A workspace with single testing agent.",
    start_messages: [
        {
            source: "testbot",
            destination: "human",
            content: "Hello."
        }
    ],
    agents: [
            {
                type: 'ToolChatAgent',
                name: 'testbot',
                instruction: 'You are testbot.'
            }
    ],
    main_channel: 'testbot'
};

workspace