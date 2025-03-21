local reachable_agents = {
  "CodeWritingAgent": "This is a skilled code writing agent proficient in various programming languages. You can write clean, efficient, and well-documented code for various applications and software projects.",
  "UIDesignAgent": "This is a UI design agent specializing in creating intuitive and visually appealing user interfaces for websites, mobile apps, and desktop applications.",
  "ContentFillingAgent": "This is a content filling agent that can help you fill in the content of your website.",
  "WebsiteDeploymentAgent": "This is a website deployment agent that can deploy a website with html, css and javascript codes."
};

local workspace = {
    title: "Automatic Website Generation",
    description: "An example workspace for generating a simple website and deploy it.",
    main_channel: 'WebDevelopmentMasterAgent',
    start_messages: [
        {
            source: "WebDevelopmentMasterAgent",
            destination: "human",
            content: "Hi. Please give me a paragraph describing the website you want to create and deploy."
        }
    ],
    agents: [
        {
            type: 'TaskCoordinatorAgent',
            name: 'WebDevelopmentMasterAgent',
            instruction: "
            Do not do any task by yourself, always try to call other agents. You should help user to create prototype software based on given description.\n
            When communicate with sub agents, always provide full HTML, CSS, JavaScript or othercodes in message. DO NOT refer to previous codes.\n
            When calling WebsiteDeploymentAgent, always provide full HTML, CSS, JavaScript or other codes in message directly. DO NOT refer to previous codes.\n
            Once you obtained a link from WebsiteDeploymentAgent, show user the link in a <a> tag with href attribute.\n
            ",
            planner: {
              type: "SimpleMultiAgentGoalPlanner",
              reachable_agents: reachable_agents
            },
            reachable_agents: reachable_agents,
        },
          {
    "type": "ConversationalTaskAgent",
    "name": "ContentFillingAgent",
    "instruction": "You are a website content filling agent that can fill text content into a website.",
    model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
  },
  {
    "type": "ConversationalTaskAgent",
    "name": "CodeWritingAgent",
    "instruction": "You are a skilled code writing agent proficient in various programming languages. You can write clean, efficient, and well-documented code for various applications and software projects.",
    model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
  },
  {
    "type": "ConversationalTaskAgent",
    "name": "UIDesignAgent",
    "instruction": "You are a UI design agent specializing in creating intuitive and visually appealing user interfaces for websites. Generate a wireframe in your design.",
    model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
  },
    {
    "type": "ConversationalTaskAgent",
    "name": "WebsiteDeploymentAgent",
    "instruction": "You are a website deployment agent that can deploy a website with html, css and javascript codes. When calling WebsiteDeploymentTool, always wrap html, css and javascript codes with ```.",
    "tools": [
      {
        "type": "WebsiteDeploymentTool"
      }
    ]
  }

    ]
};

workspace