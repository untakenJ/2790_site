<script lang="ts">
    import { onMount, onDestroy } from 'svelte';

    // User input and API response states
    let input_value = '';
    let feedback_value = '';
    let control_image: File | null = null;

    interface ApiResponse {
        category: 'generated' | 'modified' | 'refined'; // Image category
        prompt: string;
        image_url: string;
        timestamp: string; // When the image was created
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

    // Brush size state
    let brushSize = 10; // Default brush size

    // Undo stack
    let undoStack: ImageData[] = [];
    const MAX_UNDO = 20; // Maximum number of undo steps

    // Function to convert Blob to Base64 (optional for persistence)
    function blobToBase64(blob: Blob): Promise<string> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result as string);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }

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

            // Determine the category based on whether a control image was used
            let category: 'generated' | 'refined' = control_image ? 'refined' : 'generated';

            api_response = {
                category: category,
                prompt: input_value,
                image_url: imageUrl,
                timestamp: new Date().toISOString()
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

        // Get the last generated or refined image
        const lastImageEntry = history[history.length - 1];
        const lastImageUrl = lastImageEntry.image_url;

        // Fetch the blob from the last image URL
        const response = await fetch(lastImageUrl);
        const blob = await response.blob();

        // Get the modified image with annotations
        const modifiedImage = await getModifiedImage();
        if (!modifiedImage) {
            alert("Failed to create modified image.");
            return;
        }

        // Create a URL for the modified image
        const modifiedImageUrl = URL.createObjectURL(modifiedImage);

        // Add the modified image to history (Category 2)
        const modifiedApiResponse: ApiResponse = {
            category: 'modified',
            prompt: feedback_value,
            image_url: modifiedImageUrl,
            timestamp: new Date().toISOString()
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
        if (!imageElement) return;

        isDrawing = true;
        [lastX, lastY] = [event.offsetX, event.offsetY];

        // Save the current state before starting to draw
        saveState();
    }

    function draw(event: MouseEvent) {
        if (!isDrawing) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.strokeStyle = '#FF0000'; // Drawing color
        ctx.lineWidth = brushSize; // Dynamic brush size
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

    // Save the current state of the canvas for undo functionality
    function saveState() {
        if (undoStack.length >= MAX_UNDO) {
            undoStack.shift(); // Remove the oldest state
        }
        const ctx = canvas.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            undoStack.push(imageData);
        }
    }

    // Undo the last drawing action
    function undo() {
        if (undoStack.length === 0) return;
        const ctx = canvas.getContext('2d');
        if (ctx) {
            const imageData = undoStack.pop();
            if (imageData) {
                ctx.putImageData(imageData, 0, 0);
            }
        }
    }

    // Handle keyboard shortcuts
    // function handleKeyDown(event: KeyboardEvent) {
    //     // Check for Ctrl+Z or Cmd+Z
    //     if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
    //         event.preventDefault(); // Prevent the default browser undo
    //         undo();
    //     }
    // }

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

    // Handle keyboard shortcuts
    function handleKeyDown(event: KeyboardEvent) {
        console.log("Keydown event:", event);
        // Check for Ctrl+Z or Cmd+Z
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'z') {
            console.log("Ctrl/Cmd + Z detected. Triggering undo.");
            event.preventDefault(); // Prevent the default browser undo
            undo();
        }
    }

    // Add and remove the keyboard event listener using onMount's cleanup
    onMount(() => {
        console.log("Component mounted. Adding keydown event listener.");
        window.addEventListener('keydown', handleKeyDown);

        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            console.log("Component destroyed. Removing keydown event listener.");
        };
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

    /* Feedback and Controls styling */
    .feedback-section {
        margin-top: 30px;
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .feedback-section input[type="text"] {
        flex: 1;
        padding: 12px 20px;
        border: 1px solid #ccc;
        border-radius: 5px;
        font-size: 16px;
        transition: border-color 0.3s;
    }

    .feedback-section input[type="text"]:focus {
        border-color: #4A90E2;
        outline: none;
    }

    /* Brush Controls */
    .brush-controls {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-top: 10px;
    }

    .brush-controls label {
        font-size: 14px;
        color: #333;
    }

    .brush-controls input[type="range"] {
        width: 150px;
    }

    /* Undo Button */
    .undo-button {
        padding: 6px 12px;
        background-color: #FF5733; /* Orange for undo */
        color: white;
        border: none;
        border-radius: 4px;
        font-size: 14px;
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .undo-button:disabled {
        background-color: #ffb3ab;
        cursor: not-allowed;
    }

    .undo-button:hover:not(:disabled) {
        background-color: #e04e2a;
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
        cursor: pointer;
        transition: background-color 0.3s;
    }

    .history-item:hover {
        background-color: #f1f1f1;
    }

    .history-item.generated {
        border-left: 4px solid #4A90E2; /* Blue for generated */
    }

    .history-item.modified {
        border-left: 4px solid #FF5733; /* Orange for modified */
    }

    .history-item.refined {
        border-left: 4px solid #28a745; /* Green for refined */
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

    .type-and-download {
        display: flex;
        align-items: center;
        gap: 5px;
    }

    .type {
        font-size: 14px;
        color: #777;
    }

    .timestamp {
        font-size: 12px;
        color: #999;
        margin-top: 3px;
    }

    /* Responsive design */
    @media (max-width: 600px) {
        .container {
            margin: 20px;
            padding: 15px;
        }

        button, input[type="text"], input[type="file"], .brush-controls input[type="range"] {
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

        .brush-controls {
            flex-direction: column;
            align-items: flex-start;
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

    <!-- Brush Controls and Undo Button -->
    {#if history.length > 0}
        <div class="brush-controls">
            <label for="brushSize">Brush: {brushSize}px</label>
            <input
                type="range"
                id="brushSize"
                min="1"
                max="50"
                bind:value={brushSize}
                aria-label="Brush size slider"
            />
            <button class="undo-button" on:click={undo} disabled={undoStack.length === 0}>
                Undo
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
            {#each history as item, index}
                <div class="history-item {item.category}">
                    <img src={item.image_url} alt={`Image ${index + 1}`} />
                    <div class="prompt-section">
                        <p class="prompt">Prompt: {item.prompt}</p>
                        <div class="type-and-download">
                            <span class="type">
                                {#if item.category === 'generated'}
                                    Base Generation
                                {:else if item.category === 'modified'}
                                    User Modification
                                {:else if item.category === 'refined'}
                                    AI Refinement
                                {/if}
                            </span>
                        </div>
                        <p class="timestamp">Time: {new Date(item.timestamp).toLocaleString()}</p>
                    </div>
                </div>
            {/each}
        </div>
    {/if}
</div>
