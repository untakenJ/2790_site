<!-- STARTER CODE -->
<!-- <h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p> -->
<!-- route to ./routes/api_call/_page.svelte -->
<h1>Sample Input Interface</h1>

<!-- VAR DECLARATION -->
<script>
    let input_value = '';
    // Declare input_value with $state('') to trigger updates on frontend
    let curr_input = $state('');

    function updateInput() {
        curr_input = input_value
    }
</script>

<!-- INPUT FIELD / BUTTON -->
<div>
    <input
        type="text"
        bind:value={input_value}
        placeholder="Enter a string"
    />
    <button onclick={updateInput}>Update</button>
</div>

<p>Updated Input: {curr_input}</p>