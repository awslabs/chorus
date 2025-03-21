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
                type: 'ConversationalTaskAgent',
                name: 'testbot',
                instruction: 'You are testbot.'
            }
    ],
    main_channel: 'testbot'
};

workspace