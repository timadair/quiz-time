---
title: Quiz Time
emoji: 🔥
colorFrom: purple
colorTo: yellow
sdk: gradio
sdk_version: 5.44.1
app_file: app.py
pinned: false
license: apache-2.0
short_description: Use an LLM to generate a multiple choice quiz
---

# Quiz Generator

## How to Deploy
No need.  It's hosted in a Hugging Face (HF) Space at the URL I included in my e-mail.

## Architecture and AI Tool choices

### Gradio UI w/ gpt-oss-20B and no workflow framework
- **Gradio** is good for ML prototyping UIs, integrates well with HF, and is on my list of libraries I want to explore deeper.  
- The **gpt-oss-20B** LLM is new, is open source, integrated with HF, likely faster than 120B, and seems to be building a good reputation for complex reasoning, which helps with quiz question generation and JSON formatting.  
- I used just the **transformers library** with no workflow framework as a challenge to myself, since I didn't need a workflow that would return streamed tokens.  Small mistake: having to figure out for myself where the CoT ends and the final answer begins is a pain.

### Hosting: Hugging Face Spaces - Zero GPU 
I wanted my prototype to have 0 setup for the user if at all possible, and HF Spaces with ZeroGPU (dynamic resources, queue for time on an Nvidia H200) satisfies all three goals I had:
1. Don't make the user have to sign up and generate and register a key for anything.
2. Don't try to run an LLM locally on unknown hardware specs.
3. Don't use my key for a publicly-facing app.

I already have up to 25 minutes of GPU inference per day with my Pro account, so there's no extra expense for me, and the wait for a GPU is minimal.  There's a small risk of a malicious stranger using up all 25 minutes before you guys get to it. 

