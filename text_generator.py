import openai

def generate_text(prompt):
    openai.api_key = 'your-api-key-here'
    response = openai.Completion.create(
        engine="text-davinci-002",  # or any other suitable model
        prompt=prompt,
        max_tokens=150
    )
    return response.choices[0].text.strip()

if __name__ == "__main__":
    prompt_input = input("Enter a prompt: ")
    print(generate_text(prompt_input))