local sub_agents = {
  "NewsSearchAgent": "An agent that can help user to find news related to artificial intelligence and summarize them by search web and access pages.",
  "ResearchPaperSearchAgent": "An agent that can help user to find research papers and summarize them by search arxiv and access pages.",
  "MachineLearningQAAgent": "An agent that can help user to explain the concept of machine learning and artificial intelligence."
};

local workspace = {
    title: "Conversational Proxy Agent",
    description: "An example workspace that demonstrates the use of Synchronized Meta Agent for building conversational proxy agent.",
    main_channel: 'MachineLearningQARoutingAgent',
    start_messages: [
        {
            source: "MachineLearningQARoutingAgent",
            destination: "human",
            content: "Hi, I can help to answer any question related to artifacial intelligence and machine learning. I can further answer questions related to recent news and research papers."
        }
    ],
    agents: [
        {
            type: 'TaskCoordinatorAgent',
            name: 'MachineLearningQARoutingAgent',
            instruction: "Do not do any task by yourself, always try to call other agents. If there is no relevant agent available, tell the user that don't have a agent to answer the question.",
            reachable_agents: sub_agents,
        },
        {
                type: 'ConversationalTaskAgent',
                name: 'NewsSearchAgent',
                instruction: 'You can help user to find news and summarize them by search web and access pages.',
                tools: [
                    { type: 'DuckDuckGoWebSearchTool' },
                    { type: 'WebRetrieverTool' }
                ],
                model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
        },
        {
                type: 'ConversationalTaskAgent',
                name: 'ResearchPaperSearchAgent',
                instruction: 'Help user on arxiv related questions',
                tools: [
                    { type: 'ArxivRetrieverTool' }
                ],
                model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
        },
        {
                type: 'ConversationalTaskAgent',
                name: 'MachineLearningQAAgent',
                instruction: 'You can help you user expalaining the concept of machine learning and artificial intelligence. Please also attach useful code libraries whenever applicable.',
                model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
        }
    ]
};

workspace