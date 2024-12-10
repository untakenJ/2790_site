<script lang="ts">
    import { onMount, onDestroy } from 'svelte';

    // User input and API response states
    let input_value = '';
    let feedback_value = '';
    let control_image: File | null = null;

    interface ApiResponse {
        type: 'generated' | 'modified'; // Indicates the image type
        prompt: string;
        image_url: string;
    }

    let api_response: ApiResponse | null = null;
    let error = '';
    let is_loading = false;

    // History of prompts and images
    let history: ApiResponse[] = [];

    // References to the canvas and image elements
    let canvas: HTMLCanvasElement;
    let imageElement: HTMLImageElement;

    // Drawing state
    let isDrawing = false;
    let lastX = 0;
    let lastY = 0;

    // Fetch image from Stability API based on user prompt and optional control image
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
            formData.append("height", '1024'); // Default height for style endpoint
            formData.append("width", '1024');  // Default width for style endpoint

            // Determine the endpoint based on the presence of a control image
            const endpoint = control_image 
                ? "https://api.stability.ai/v2beta/stable-image/control/style" 
                : "https://api.stability.ai/v2beta/stable-image/generate/core";

            if (control_image) {
                formData.append("image", control_image);
                // Optionally, add other parameters like fidelity, aspect_ratio, etc.
                formData.append("fidelity", '0.5'); // Example fidelity
                formData.append("aspect_ratio", '1:1'); // Example aspect ratio
                formData.append("output_format", 'png'); // Example output format
            } else {
                // If using the core endpoint, you might have different or additional parameters
                formData.append("negative_prompt", ""); // Example of adding a negative prompt
            }

            const response = await fetch(endpoint, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${import.meta.env.VITE_STABILITY_KEY}`, // Stability API Key
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

            // Determine the type based on whether a control image was used
            const imageType: 'generated' | 'modified' = control_image ? 'modified' : 'generated';

            api_response = {
                type: imageType,
                prompt: input_value,
                image_url: imageUrl
            };

            // Add to history
            history = [...history, api_response];
        } catch (err) {
            if (err instanceof Error) {
                error = err.message;
            } else {
                error = "An unknown error occurred";
            }
        } finally {
            is_loading = false;
            input_value = ''; // Clear input after submission
            control_image = null; // Reset control image after submission
            if (canvas && imageElement) {
                const ctx = canvas.getContext('2d');
                if (ctx) {
                    ctx.clearRect(0, 0, canvas.width, canvas.height);
                }
            }
        }
    }

    // Handle image upload
    function handleImageUpload(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files[0]) {
            control_image = target.files[0];
        }
    }

    // Handle feedback submission
    async function submitFeedback() {
        if (!feedback_value.trim()) {
            alert("Please enter your feedback.");
            return;
        }

        if (history.length === 0) {
            alert("Generate an image first before providing feedback.");
            return;
        }

        // Get the last generated image URL
        const lastImage = history[history.length - 1].image_url;

        // Fetch the blob from the last image URL
        const response = await fetch(lastImage);
        const blob = await response.blob();

        // Get the modified image with annotations
        const modifiedImage = await getModifiedImage();
        if (!modifiedImage) {
            alert("Failed to create modified image.");
            return;
        }

        // Create a URL for the modified image
        const modifiedImageUrl = URL.createObjectURL(modifiedImage);

        // Add the modified image to history
        const modifiedApiResponse: ApiResponse = {
            type: 'modified',
            prompt: feedback_value,
            image_url: modifiedImageUrl
        };
        history = [...history, modifiedApiResponse];

        // Set the modified image as the control image for the next API call
        control_image = modifiedImage;
        input_value = feedback_value;
        feedback_value = '';

        // Call the API to generate a new image based on the modified image
        await callAPI();
    }

    // Combine the original image and the canvas drawing into a single image
    async function getModifiedImage(): Promise<File | null> {
        if (!canvas || !imageElement) return null;

        // Create an off-screen canvas to combine image and drawings
        const offCanvas = document.createElement('canvas');
        const offCtx = offCanvas.getContext('2d');
        if (!offCtx) return null;

        offCanvas.width = imageElement.naturalWidth;
        offCanvas.height = imageElement.naturalHeight;

        // Draw the original image
        offCtx.drawImage(imageElement, 0, 0, offCanvas.width, offCanvas.height);

        // Draw the user's annotations scaled to the original image size
        offCtx.drawImage(canvas, 0, 0, offCanvas.width, offCanvas.height);

        // Convert to Blob and then to File
        return new Promise((resolve) => {
            offCanvas.toBlob((blob) => {
                if (blob) {
                    const file = new File([blob], "modified_image.png", { type: "image/png" });
                    resolve(file);
                } else {
                    resolve(null);
                }
            }, "image/png");
        });
    }

    // Handle drawing events
    function startDrawing(event: MouseEvent) {
        isDrawing = true;
        [lastX, lastY] = [event.offsetX, event.offsetY];
    }

    function draw(event: MouseEvent) {
        if (!isDrawing) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.strokeStyle = '#FF0000'; // Drawing color
        ctx.lineWidth = 2;
        ctx.lineJoin = 'round';
        ctx.lineCap = 'round';

        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(event.offsetX, event.offsetY);
        ctx.stroke();
        [lastX, lastY] = [event.offsetX, event.offsetY];
    }

    function stopDrawing() {
        isDrawing = false;
    }

    // Set up canvas dimensions to match the image
    function setupCanvas() {
        if (imageElement && canvas) {
            canvas.width = imageElement.clientWidth;
            canvas.height = imageElement.clientHeight;
        }
    }

    // Ensure canvas is set up when image loads
    function handleImageLoad() {
        setupCanvas();
    }

    // Clean up event listeners if any
    onDestroy(() => {
        // Any necessary cleanup
    });
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

    input[type="text"], input[type="file"] {
        padding: 12px 20px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
        transition: border-color 0.3s;
    }

    input[type="text"]:focus, input[type="file"]:focus {
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

    .image-container {
        position: relative;
        display: inline-block;
    }

    .image-container img {
        max-width: 100%;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    canvas {
        position: absolute;
        top: 0;
        left: 0;
        cursor: crosshair;
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

    /* History styling */
    .history {
        margin-top: 40px;
    }

    .history-item {
        display: flex;
        align-items: center;
        gap: 15px;
        margin-bottom: 20px;
        padding: 10px;
        background-color: #ffffff;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .history-item.generated {
        border-left: 4px solid #4A90E2; /* Blue for generated */
    }

    .history-item.modified {
        border-left: 4px solid #FF5733; /* Orange for modified */
    }

    .history-item img {
        width: 100px;
        height: auto;
        border-radius: 5px;
        object-fit: cover;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    .prompt-section {
        display: flex;
        flex-direction: column;
    }

    .prompt-section .prompt {
        font-size: 16px;
        color: #333;
        margin: 0;
    }

    .prompt-section .type {
        font-size: 14px;
        color: #777;
        margin-top: 5px;
    }

    /* Feedback section */
    .feedback-section {
        margin-top: 30px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .feedback-section input[type="text"] {
        flex: 1;
    }

    /* Responsive design */
    @media (max-width: 600px) {
        .container {
            margin: 20px;
            padding: 15px;
        }

        button, input[type="text"], input[type="file"] {
            font-size: 14px;
            padding: 10px 15px;
        }

        .history-item {
            flex-direction: column;
            align-items: flex-start;
        }

        .history-item img {
            width: 100%;
        }
    }
</style>

<div class="container">
    <h1>Image Interaction</h1>

    <!-- Input field, image upload, and generate button -->
    <div class="input-group">
        <input
            type="text"
            bind:value={input_value}
            placeholder="Enter image prompt"
            aria-label="Image prompt"
        />
        <input
            type="file"
            accept="image/*"
            on:change={handleImageUpload}
            aria-label="Upload control image (optional)"
        />
        <button on:click={callAPI} disabled={is_loading}>
            {is_loading ? 'Generating...' : 'Generate Image'}
        </button>
    </div>

    <!-- Feedback section -->
    {#if history.length > 0}
        <div class="feedback-section">
            <h3>Refinement Feedback:</h3>
            <input
                type="text"
                bind:value={feedback_value}
                placeholder="Enter feedback prompt"
                aria-label="Feedback prompt"
            />
            <button on:click={submitFeedback} disabled={is_loading}>
                {is_loading ? 'Refining...' : 'Submit Feedback'}
            </button>
        </div>
    {/if}

    <!-- Display loading, error, or API response -->
    {#if is_loading && history.length === 0}
        <p class="message">Loading...</p>
    {:else if error}
        <p class="message error">Error: {error}</p>
    {:else if api_response}
        <div class="response">
            <h2>Prompt: {api_response.prompt}</h2>
            <div class="image-container">
                <img
                    bind:this={imageElement}
                    src={api_response.image_url}
                    alt="Generated Image"
                    on:load={handleImageLoad}
                />
                <canvas
                    bind:this={canvas}
                    on:mousedown={startDrawing}
                    on:mousemove={draw}
                    on:mouseup={stopDrawing}
                    on:mouseout={stopDrawing}
                ></canvas>
            </div>
        </div>
    {/if}

    <!-- History of generated and modified images -->
    {#if history.length > 1}
        <div class="history">
            <h3>History</h3>
            {#each history.slice(0, history.length - 1) as item, index}
                <div class="history-item {item.type}">
                    <img src={item.image_url} alt={`Image ${index + 1}`} />
                    <div class="prompt-section">
                        <p class="prompt">Prompt: {item.prompt}</p>
                        <p class="type">{item.type === 'generated' ? 'AI Generated' : 'User Modified'}</p>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
