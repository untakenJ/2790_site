<!-- STARTER CODE -->
<!-- <h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p> -->
<h1>API Demo</h1>
<!-- home routing: -->
<p><a href = './'>Home</a></p>
<p><a href="./api_call">API Call Demo</a></p>

<!-- VAR DECLARATION -->
<script>
    // import ApiResponse from '$lib/components/ApiResponse.svelte';
    // let api_response = writable('');

    // (When we don't need an immediate update within our DOM, we can use a regular variable)
    let input_value = '';
    // Declare input_value with $state('') to trigger updates on frontend
    let curr_input = $state('');

    async function callAPI() {
        if (!input_value.trim()) {
            alert("Please enter a valid title.");
            return;
        }

        
    }

</script>

<!-- INPUT FIELD / BUTTON -->
<div>
    <input
        type="text"
        bind:value={input_value}
        placeholder="Enter string for API call"
    />
    <button onclick={callAPI}>Call API</button>
</div>
