from chorus.agents.tool_chat_agent import ConversationalTaskAgent
from chorus.core import Chorus
from chorus.toolbox import WebRetrieverTool, DuckDuckGoWebSearchTool
from chorus.helpers.communication import CommunicationHelper
from chorus.helpers.smart_logic import SmartLogicHelper


if __name__ == '__main__':
    # Create specialized agents for different aspects of website creation
    content_agent = ConversationalTaskAgent(
        instruction="""
        You are a skilled content writer. Create engaging website content based on the requirements.
        Return your content in a structured format with clear section labels.
        Focus on compelling copy that converts visitors into customers.
        """,
        tools=[DuckDuckGoWebSearchTool(), WebRetrieverTool()]
    ).name("ContentWriter")

    designer_agent = ConversationalTaskAgent(
        instruction="""
        You are a website designer. Based on the content provided, create design specifications including:
        - Color scheme (provide exact hex codes)
        - Typography choices (specify font families)
        - Layout structure (describe component positioning)
        - Visual hierarchy
        - Spacing and padding guidelines
        Return your design specs in a structured format that the developer can implement.
        """
    ).name("Designer")

    developer_agent = ConversationalTaskAgent(
        instruction="""
        You are a web developer. Based on the content provided, create a preliminary implementation:
        - Create clean, semantic HTML5 structure
        - Set up basic CSS3 with flexbox/grid
        - Ensure mobile-first approach
        - Focus on core functionality
        You will receive design specs to refine the implementation later.
        Return the complete HTML and CSS code for the website.
        """
    ).name("Developer")

    qa_agent = ConversationalTaskAgent(
        instruction="""
        You are a QA engineer. Review the complete website implementation and check for:
        - HTML/CSS validation
        - Responsive design issues
        - Content accuracy
        - Design implementation accuracy
        - Cross-browser compatibility concerns
        Return a detailed review with any issues found and suggestions for improvements.
        Start your response with a summary line: "CRITICAL ISSUES: Yes/No"
        """
    ).name("QAEngineer")

    chorus = Chorus(agents=[content_agent, designer_agent, developer_agent, qa_agent])
    chorus.start()

    # Create communication helper
    comm = CommunicationHelper(chorus.get_global_context())
    logic = SmartLogicHelper(chorus.get_global_context())

    # Step 1: Content Creation (Sequential)
    print("Step 1: Creating content...")
    content_response = comm.send_and_wait(
        destination="ContentWriter",
        content="Create content for a coffee shop landing page including: hero section with main value proposition, about us section highlighting our artisanal approach, and contact information section."
    )
    print("\nContent Created:")
    print(content_response.content)

    # Step 2: Parallel Design and Initial Development
    print("\nStep 2: Starting parallel design and initial development...")
    
    # Send tasks to both designer and developer simultaneously
    comm.send(
        destination="Designer",
        content=f"Create design specifications for this coffee shop website with the following content:\n{content_response.content}"
    )
    
    comm.send(
        destination="Developer",
        content=f"Create an initial implementation based on this content. Focus on structure and basic styling:\n{content_response.content}"
    )

    # Wait for both responses
    design_response = comm.wait(source="Designer")
    dev_initial_response = comm.wait(source="Developer")
    
    print("\nDesign Specifications Created:")
    print(design_response.content)
    print("\nInitial Development Complete:")
    print(dev_initial_response.content)

    # Step 3: Final Development with Design Specs (Sequential)
    print("\nStep 3: Refining implementation with design specifications...")
    final_dev_response = comm.send_and_wait(
        destination="Developer",
        content=f"Refine your implementation using these design specifications:\n{design_response.content}\n\nYour initial implementation:\n{dev_initial_response.content}"
    )
    print("\nFinal Implementation Complete:")
    print(final_dev_response.content)

    # Step 4: QA Review and Refinement Loop
    max_iterations = 3
    current_iteration = 0
    current_implementation = final_dev_response.content

    while current_iteration < max_iterations:
        print(f"\nQA Review Iteration {current_iteration + 1}...")
        qa_response = comm.send_and_wait(
            destination="QAEngineer",
            content=f"Review this website implementation:\n{current_implementation}\n\nAgainst these design specifications:\n{design_response.content}\n\nAnd this content:\n{content_response.content}"
        )
        print("\nQA Review Complete:")
        print(qa_response.content)

        # Use smart_judge to check if there are critical issues
        has_critical_issues = logic.smart_judge(
            qa_response.content,
            "Does the QA review indicate any critical issues that require immediate attention?"
        )

        if not has_critical_issues:
            print("\nNo critical issues found. Website implementation is complete!")
            break

        if current_iteration < max_iterations - 1:
            print("\nCritical issues found. Sending for refinement...")
            dev_response = comm.send_and_wait(
                destination="Developer",
                content=f"Please address these QA issues and refine the implementation:\n{qa_response.content}\n\nCurrent implementation:\n{current_implementation}"
            )
            current_implementation = dev_response.content
            print("\nRefinement Complete:")
            print(current_implementation)
        
        current_iteration += 1

    if current_iteration == max_iterations:
        print("\nReached maximum refinement iterations. Please review the final implementation manually.")

    chorus.stop()
