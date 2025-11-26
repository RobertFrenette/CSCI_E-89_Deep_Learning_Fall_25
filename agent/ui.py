"""
Gradio UI Module for RAG Chatbot
Handles all UI creation and layout
"""

import os
import gradio as gr
from agent import config

def create_interface(app):
    """
    Create and configure the Gradio interface.
    
    Params:
        app: RAGChatbotApp instance with methods: process_query, clear_conversation
    
    Returns:
        Gradio Blocks interface
    """
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "shield.png")
    
    with gr.Blocks(title="AI Agent Insure - Agent Assist") as demo:
        # Header with logo and title side by side
        with gr.Row():
            with gr.Column(scale=1, min_width=100):
                gr.Image(logo_path, show_label=False, 
                        container=False, height=80, width=80)
            with gr.Column(scale=9):
                gr.Markdown(f"# {config.APP_TITLE}")
        
        gr.Markdown(config.APP_DESCRIPTION)
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### Input")
                text_input = gr.Textbox(
                    label="Type your question",
                    placeholder="What would you like to know?",
                    lines=2
                )
                audio_input = gr.Audio(
                    label="Or speak your question",
                    type="filepath",
                    sources=["microphone", "upload"]
                )
                submit_btn = gr.Button("Submit", variant="primary")
                clear_btn = gr.Button("Clear Conversation")
            
            with gr.Column():
                gr.Markdown("### Response")
                text_output = gr.Textbox(
                    label="Answer",
                    lines=10
                )
                audio_output = gr.Audio(
                    label="Listen to response",
                    type="filepath"
                )
        
        gr.Markdown("### Example Questions")
        gr.Examples(
            examples=[[q] for q in config.EXAMPLE_QUESTIONS],
            inputs=text_input
        )
        
        # Event handlers - wire up app methods
        submit_btn.click(
            fn=app.process_query,
            inputs=[text_input, audio_input],
            outputs=[text_input, text_output, audio_output]
        )
        
        clear_btn.click(
            fn=app.clear_conversation,
            outputs=[text_input, audio_input, text_output, audio_output]
        )
    
    return demo
