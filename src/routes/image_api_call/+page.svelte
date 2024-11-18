<script lang="ts">
    // User input and API response states
    let input_value = '';
    interface ApiResponse {
        prompt: string;
        image_url: string;
    }
    let api_response: ApiResponse | null = null;
    let error = '';
    let is_loading = false;

    // Fetch image from Stability API based on user prompt
    async function callAPI() {
        if (!input_value.trim()) {
            alert("Please enter a prompt.");
            return;
        }

        is_loading = true;
        error = '';
        api_response = null;

        try {
            // Prepare form data
            const formData = new FormData();
            formData.append("prompt", input_value);
            formData.append("height", '512');
            formData.append("width", '512');

            const response = await fetch("https://api.stability.ai/v2beta/stable-image/generate/core", {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${import.meta.env.VITE_STABILITY_KEY}`, // Stability API Key,
                    "Accept": "image/*"
                },
                body: formData
            });

            if (!response.ok) {
                // Attempt to parse and log the error response for debugging
                const errorText = await response.text();
                console.error("API Error Response:", errorText);

                throw new Error(`Failed to fetch image from Stability AI: ${errorText}`);
            }

            // Convert the binary image response to an object URL
            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);

            api_response = {
                prompt: input_value,
                image_url: imageUrl
            };
        } catch (err) {
            if (err instanceof Error) {
                error = err.message;
            } else {
                error = "An unknown error occurred";
            }
        } finally {
            is_loading = false;
        }
    }
</script>

<style>
    /* Container styling */
    .container {
        max-width: 800px;
        margin: 50px auto;
        padding: 20px;
        background-color: #f9fafb;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        font-family: 'Arial', sans-serif;
    }

    h1 {
        text-align: center;
        color: #333;
        margin-bottom: 30px;
    }

    /* Input and button styling */
    .input-group {
        display: flex;
        flex-direction: column;
        gap: 15px;
        margin-bottom: 20px;
    }

    input[type="text"] {
        padding: 12px 20px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
        transition: border-color 0.3s;
    }

    input[type="text"]:focus {
        border-color: #4A90E2;
        outline: none;
    }

    button {
        padding: 12px 20px;
        background-color: #4A90E2;
        color: white;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    button:disabled {
        background-color: #a0c4e3;
        cursor: not-allowed;
    }

    button:hover:not(:disabled) {
        background-color: #357ABD;
    }

    /* Response styling */
    .response {
        text-align: center;
        margin-top: 30px;
    }

    .response h2 {
        color: #333;
        margin-bottom: 15px;
    }

    .response img {
        max-width: 100%;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Loading and error messages */
    .message {
        text-align: center;
        font-size: 18px;
        color: #555;
        margin-top: 20px;
    }

    .error {
        color: #E74C3C;
    }

    /* Responsive design */
    @media (max-width: 600px) {
        .container {
            margin: 20px;
            padding: 15px;
        }

        button, input[type="text"] {
            font-size: 14px;
            padding: 10px 15px;
        }
    }
</style>

<div class="container">
    <h1>Base Image Generator</h1>

    <!-- Input field and button -->
    <div class="input-group">
        <input
            type="text"
            bind:value={input_value}
            placeholder="Enter image prompt"
            aria-label="Image prompt"
        />
        <button on:click={callAPI} disabled={is_loading}>
            {is_loading ? 'Generating...' : 'Generate Image'}
        </button>
    </div>

    <!-- Display loading, error, or API response -->
    {#if is_loading}
        <p class="message">Loading...</p>
    {:else if error}
        <p class="message error">Error: {error}</p>
    {:else if api_response}
        <div class="response">
            <h2>Prompt: {api_response.prompt}</h2>
            <img src={api_response.image_url} alt="Generated Image" />
        </div>
    {/if}
</div>
