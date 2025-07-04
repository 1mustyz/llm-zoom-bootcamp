import json
import re
from typing import List, Dict, Any, Optional

class ChatAgent:
    def __init__(self, gemini_client, index, max_iterations: int = 3):
        self.gemini_client = gemini_client
        self.index = index
        self.max_iterations = max_iterations
        self.conversation_history = []
        self.prompt_template = """
You're a course teaching assistant.
You're given a QUESTION from a course student and that you need to answer with your own knowledge and provided CONTEXT.
The CONTEXT is build with the documents from our FAQ database.
SEARCH_QUERIES contains the queries that were used to retrieve the documents
from FAQ to and add them to the context.
PREVIOUS_ACTIONS contains the actions you already performed.
CONVERSATION_HISTORY contains the previous questions and answers from this chat session.
At the beginning the CONTEXT is empty.
You can perform the following actions:
- Search in the FAQ database to get more data for the CONTEXT
- Answer the question using the CONTEXT
- Answer the question using your own knowledge
For the SEARCH action, build search requests based on the CONTEXT and the QUESTION.
Carefully analyze the CONTEXT and generate the requests to deeply explore the topic. 
Don't use search queries used at the previous iterations.
Don't repeat previously performed actions.
Don't perform more than {max_iterations} iterations for a given student question.
The current iteration number: {iteration_number}. If we exceed the allowed number 
of iterations, give the best possible answer with the provided information.
Output templates:
If you want to perform search, use this template:
{{
"action": "SEARCH",
"reasoning": "<add your reasoning here>",
"keywords": ["search query 1", "search query 2", ...]
}}
If you can answer the QUESTION using CONTEXT, use this template:
{{
"action": "ANSWER_CONTEXT",
"answer": "<your answer>",
"source": "CONTEXT"
}}
If the context doesn't contain the answer, use your own knowledge to answer the question
{{
"action": "ANSWER",
"answer": "<your answer>",
"source": "OWN_KNOWLEDGE"
}}
<QUESTION>
{question}
</QUESTION>
<SEARCH_QUERIES>
{search_queries}
</SEARCH_QUERIES>
<CONTEXT> 
{context}
</CONTEXT>
<PREVIOUS_ACTIONS>
{previous_actions}
</PREVIOUS_ACTIONS>
<CONVERSATION_HISTORY>
{conversation_history}
</CONVERSATION_HISTORY>
""".strip()

    def agentic_search(self, question: str) -> Dict[str, Any]:
        """Process a single question using agentic search"""
        search_queries = []
        search_results = []
        previous_actions = []
        iteration = 0
        
        print(f'\n🔍 Processing: "{question}"')
        
        while True:
            print(f'ITERATION #{iteration}...')
        
            context = self.build_context(search_results)
            prompt = self.prompt_template.format(
                question=question,
                context=context,
                search_queries="\n".join(search_queries),
                previous_actions='\n'.join([json.dumps(a) for a in previous_actions]),
                conversation_history=self.format_conversation_history(),
                max_iterations=self.max_iterations,
                iteration_number=iteration
            )
        
            answer_json = self.llm(prompt)
            cleaned_answer = re.sub(r"^```(?:json)?|```$", "", answer_json.strip(), flags=re.MULTILINE)
            answer = json.loads(cleaned_answer)
            previous_actions.append(answer)
        
            action = answer['action']
            if action != 'SEARCH':
                break
        
            keywords = answer['keywords']
            search_queries = list(set(search_queries) | set(keywords))
            for k in keywords:
                res = self.search(k)
                search_results.extend(res)
        
            search_results = self.dedup(search_results)
            
            iteration = iteration + 1
            if iteration >= self.max_iterations + 1:
                break
        
            print()
        
        return answer

    def add_to_history(self, question: str, answer: Dict[str, Any]):
        """Add question and answer to conversation history"""
        self.conversation_history.append({
            'question': question,
            'answer': answer.get('answer', 'No answer provided'),
            'source': answer.get('source', 'UNKNOWN')
        })

    def format_conversation_history(self) -> str:
        """Format conversation history for the prompt"""
        if not self.conversation_history:
            return "No previous conversation."
        
        formatted = []
        for i, entry in enumerate(self.conversation_history, 1):
            formatted.append(f"Q{i}: {entry['question']}")
            formatted.append(f"A{i}: {entry['answer']} (Source: {entry['source']})")
        
        return "\n".join(formatted)

    def chat(self):
        """Main chat loop"""
        print("🤖 Course Teaching Assistant Chat")
        print("=" * 50)
        print("Hello! I'm your course teaching assistant. Ask me any questions about the course.")
        print("Type 'quit', 'exit', or 'bye' to end the conversation.")
        print("Type 'history' to see our conversation history.")
        print("Type 'clear' to clear the conversation history.")
        print("-" * 50)
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Check for exit commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Goodbye! Feel free to come back if you have more questions.")
                    break
                
                # Handle special commands
                if user_input.lower() == 'history':
                    self.show_history()
                    continue
                
                if user_input.lower() == 'clear':
                    self.clear_history()
                    continue
                
                # Skip empty input
                if not user_input:
                    print("Please enter a question or command.")
                    continue
                
                # Process the question
                print(f"\n🤖 Assistant: Let me help you with that...")
                answer = self.agentic_search(user_input)
                
                # Display the answer
                print(f"\n💡 Answer: {answer.get('answer', 'I apologize, but I could not generate an answer.')}")
                if 'source' in answer:
                    print(f"📚 Source: {answer['source']}")
                
                # Add to conversation history
                self.add_to_history(user_input, answer)
                
            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ An error occurred: {str(e)}")
                print("Please try again with a different question.")

    def show_history(self):
        """Display conversation history"""
        if not self.conversation_history:
            print("\n📝 No conversation history yet.")
            return
        
        print(f"\n📝 Conversation History ({len(self.conversation_history)} exchanges):")
        print("-" * 50)
        for i, entry in enumerate(self.conversation_history, 1):
            print(f"{i}. Q: {entry['question']}")
            print(f"   A: {entry['answer'][:100]}{'...' if len(entry['answer']) > 100 else ''}")
            print(f"   Source: {entry['source']}")
            print()

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history.clear()
        print("\n🗑️ Conversation history cleared.")

    def build_context(self, search_results: List[Any]) -> str:
        """Build context from search results"""
        if not search_results:
            return "No context available."
        
        context_parts = []
        for result in search_results:
            # Assuming your search results have text content
            # Adjust this based on your actual search result structure
            if isinstance(result, dict):
                # Extract relevant fields from the search result
                text = result.get('text', '') or result.get('content', '') or str(result)
                if text.strip():
                    context_parts.append(text.strip())
            else:
                context_parts.append(str(result))
        
        return "\n\n".join(context_parts)

    def search(self, query: str) -> List[Any]:
        """Search the FAQ database"""
        print(f"  🔍 Searching for: {query}")
        boost = {'question': 3.0, 'section': 0.5}
        results = self.index.search(
            query=query,
            filter_dict={'course': 'data-engineering-zoomcamp'},
            boost_dict=boost,
            num_results=5,
            output_ids=True
        )
        return results

    def dedup(self, results: List[Any]) -> List[Any]:
        """Remove duplicates from search results"""
        seen = set()
        result = []
        for el in results:
            _id = el['_id']
            if _id in seen:
                continue
            seen.add(_id)
            result.append(el)
        return result

    def llm(self, prompt: str) -> str:
        """Call the language model"""
        print("  🧠 Calling LLM...")
        response = self.gemini_client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )
        return response.text