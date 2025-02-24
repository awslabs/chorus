local reachable_agents = {
    "FinancialStatementRetriever": "This is an agent helps to retrieve financial statements of the company",
    "SentimentRiskAnalyzerAgent": "This is an agent analyzes the sentiment of the company's news and social media posts",
    "ManagementRiskAnalyzerAgent": "This is an agent analyzes the management team's recent change, performance, and reputation",
    "FinancialHealthAnalyzerAgent": "This is an agent helping to analyze the company's financial health risk such as long-term liquidity, debt, and cash flow",
    "GlobalEconomyAnalyzerAgent": "This is an agent helping to analyze company's risk exposure to the global economy such as GDP, inflation, and interest rates",
};

local workspace = {
    title: "Financial Risk Analysis Workspace",
    description: "An example workspace for financial risk analysis for a certain company.",
    main_channel: 'team:FinancialRiskAnalysisTeam',
    start_messages: [
        {
            source: "team:FinancialRiskAnalysisTeam",
            destination: "human",
            content: "Hi. Please give me a company name."
        }
    ],
    teams: [
        {
            type: "Team",
            name: "FinancialRiskAnalysisTeam",
            collaboration: {
                type: "CentralizedCollaboration",
                coordinator: "RiskAnalysisCoordinator"
            },
            agents: [
                {
                    type: 'FinancialAnalysisCoordinatorAgent',
                    name: 'RiskAnalysisCoordinator',
                    instruction: |||
                        Given a company name or its stock symbol, coordinate with several agenst to generate a comprehensive risk analysis report.
                        Notes:
                        - Call FinancialStatementRetriever to retrieve the company's financial statements first.
                        - When you talk to a sub agent, include the financial result when you think it is relevant.
                        - For each section, provide as much details as possible.
                        - In your final response back to human, generate a comprehensive report as your final response with simple HTML, follow this format:
                            <report>
                            <h2>Risk Analysis Report for Company XYZ</h2>

                            <h3>Summary</h3>
                            <p> ... </p>

                            <h3>Financial Health Risks</h3>
                            <p> ... </p>

                            <h3>Global Economic Risks</h3>
                            <p> ... </p>

                            <h3>Management Risks</h3>
                            <p> ... </p>

                            <h3>Sentiment Risks</h3>
                            <p> ... </p>

                            <h3>References</h3>
                            <p><ul>
                              <li><a href="...">...</a></li>
                              ...
                            </ul></p>
                            </report>
                        - You can insert charts into the report using <img/> tag.
                    |||,
                    reachable_agents: reachable_agents,
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "SentimentRiskAnalyzerAgent",
                    instruction: |||
                        You are a sentiment risk analyzer.
                        Search for news, articles and social media posts related to the company and analyze the sentiment of them.
                        Provide a summary of analysis results and findings.

                        Notes:
                        - You can include URLs of useful charts, images and relevant articles in your response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "ManagementRiskAnalyzerAgent",
                    instruction: |||
                        You are a management risk analyzer.
                        Gather information from the management team such as recent changes, performance, and reputation.
                        Provide a summary of analysis results and findings.

                        Notes:
                        - You can include URLs of useful charts, images and relevant articles in your response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "FinancialHealthAnalyzerAgent",
                    instruction: |||
                        You are a financial health analyzer.
                        Gather information from the company's financial statements such as long-term liquidity, debt, and cash flow.
                        Analyze the risk of the company's financial health.
                        Provide a summary of analysis results and findings.

                        Notes:
                        - You can include URLs of useful charts, images and relevant articles in your response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "GlobalEconomyAnalyzerAgent",
                    instruction: |||
                        You are a global economy analyzer.
                        Gather information from the global economy such as GDP, inflation, and interest rates.
                        Analyze the risk exposure of the company to these factors.
                        Provide a summary of analysis results and findings.

                        Notes:
                        - You can include URLs of useful charts, images and relevant articles in your response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "ProductAnalyzerAgent",
                    instruction: |||
                        You are a product analyzer.
                        Gather information from the web about the product to analyze its growth potential and risk.
                        Provide a summary of analysis results and findings.
                        Browse at least 30 web pages before you make a conclusion

                        Notes:
                        - You can include URLs of useful charts, images and relevant articles in your response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
                {
                    type: "ToolChatAgent",
                    name: "FinancialStatementRetriever",
                    instruction: |||
                        You are a financial statement retriever.
                        Your job is to search and retrieve the company financial statements. You can read remote PDF file and return the content.
                        Generate a comprehensive report of the financial statements including as much details as possible in your final response.
                    |||,
                    tools: [
                        { "type": "SerperWebSearchTool" },
                        { "type": "WebRetrieverToolV2" },
                        { "type": "RemotePDFReaderTool" }
                    ],
                    model_name: "anthropic.claude-3-5-sonnet-20240620-v1:0"
                },
            ]
        }
    ]
};

workspace