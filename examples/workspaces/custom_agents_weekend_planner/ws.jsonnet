local workspace = {
    title: "Weekend Trip Planner",
    description: "Recommend a trip plan for weekend considering budget, safety, experience and weather.",
    main_channel: 'Planner',
    start_messages: [
        {
            source: "Planner",
            destination: "human",
            content: "Hi, this is a weekend planning agent. I can suggest best location for a short trip for this weekend. Just describe what is approximately the area you want to explore this week!"
        }
    ],
    agents: [
        {
            type: 'MyTripCityRecommendationAgent',
            name: 'Planner',
            geo_expert: 'GeoExpert',
            advisors: [
                'BudgetAdvisor',
                'ExperienceAdvisor',
                'SafetyAdvisor'
            ]
        },
        {
            type: 'ToolChatAgent',
            name: 'WeatherInvestigationAgent',
            instruction: 'You are WeatherInvestigationAgent. You will be given a list of locations, and dates. Generate mocked weather information, including weather, temperature and humidity of all locations on single day in JSON list format. Response must be an parsable json list.',
            model_name: 'anthropic.claude-3-haiku-20240307-v1:0'
        },
        {
            type: 'ToolChatAgent',
            name: 'GeoExpert',
            instruction: 'You are GeoExpert, an expert knowing the best cities and locations for travelling.'
        }, {
            type: 'ToolChatAgent',
            name: 'BudgetAdvisor',
            instruction: 'You are BudgetAdvisor, you only provide advice and recommendation from budget perspective.'
        }, {
            type: 'ToolChatAgent',
            name: 'ExperienceAdvisor',
            instruction: 'You are ExperienceAdvisor, you only provide advice and recommendation based on trip experience for certain locations.'
        },{
            type: 'ToolChatAgent',
            name: 'SafetyAdvisor',
            instruction: 'You are SafetyAdvisor, you only provide advice and recommendation from safety perspective.'
        }
    ]
};

workspace