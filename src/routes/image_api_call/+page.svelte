<h1>Stable Diffusion Image Generator</h1>

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
            // console.log("API key: " + "(defined))");

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

<!-- Input field and button -->
<div>
    <input bind:value={input_value} placeholder="Enter your image prompt" />
    <button on:click={callAPI} disabled={is_loading}>Generate Image</button>
</div>

<!-- Display loading, error, or API response -->
{#if is_loading}
    <p>Loading...</p>
{:else if error}
    <p>Error: {error}</p>
{:else if api_response}
    <div>
        <h2>Prompt: {api_response.prompt}</h2>
        <img src={api_response.image_url} alt="(Stable Diffusion Image)" style="width: 40%; height: 40;"/>
    </div>
{/if}
