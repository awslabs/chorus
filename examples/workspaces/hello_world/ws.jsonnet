local workspace = {
    title: "My Hello World Workspace",
    description: "A simple workspace with a agent team for answering fitness related questions.",
    teams: [
        {
            type: "Team",
            name: "HelloWorldTeam",
            agents: [
                {
                    type: "TaskCoordinatorAgent",
                    name: "FitnessAnsweringAgent",
                    instruction: |||
                        Do not do any task by yourself, always try to call other agents. 
                        If there is no relevant agent available, tell the user that you do not have a agent to answer the question.
                        Make your answer comprehensive and detailed.
                    |||
                    ,
                    reachable_agents: {
                        "FactResearchAgent": "An agent that can help user to find facts related to fitness and summarize them by search web and access pages.",
                        "KnowledgeAgent": "An agent that can help user to answer general questions about fitness."
                    }
                },
                {
                    type: "ConversationalTaskAgent",
                    name: "FactResearchAgent",
                    instruction: "You can help user to find facts related to fitness and summarize them by search web and access pages.",
                    tools: [
                        {"type": "DuckDuckGoWebSearchTool"},
                        {"type": "WebRetrieverTool"}
                    ]
                },
                {
                    type: "ConversationalTaskAgent",
                    name: "KnowledgeAgent",
                    instruction: "Help user to answer general questions about fitness, nutrition, exercise and healthy lifestyle.",
                }
            ],
            collaboration: {
                type: "CentralizedCollaboration",
                coordinator: "FitnessAnsweringAgent"
            }
        }   
    ]   
};

workspace