<!-- STARTER CODE -->
<!-- <h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p> -->
<!-- home routing: -->
<!-- <p><a href = './'>Home</a></p>
<p><a href="./base_api_call">Base API Call Demo</a></p> -->

<h1>Base API Demo</h1>

<!-- VAR DECLARATION -->
<script>
    // import ApiResponse from '../../lib/compo
    // let api_response = writable('');

    // (When we don't need an immediate update within our DOM, we can use a regular variable)
    let input_value = $state('');
    // Declare input_value with $state('') to trigger updates on frontend
    let curr_input = $state('');

    let api_response = $state('');
    let error = $state('');
    let is_loading = $state(false);

    async function callAPI() {
        if (!input_value.trim()) {
            alert("Please enter a valid title.");
            return;
        }

        is_loading = true;
        error = '';
        api_response = '';

        try {
            let response = await fetch('https://jsonplaceholder.typicode.com/posts', {
                method: 'POST',
                headers: {
                    'Content-type': 'application/json; charset=UTF-8',
                },
                body: JSON.stringify({
                    title: input_value
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to fetch data');
            }

            let data = await response.json();
            api_response = data;
        } catch (err) {
            if (err instanceof Error) {
                error = err.message;
            } else {
                error = 'An unknown error occurred';
            }
        } finally {
            is_loading = false;
        }


    }

</script>

<!-- INPUT FIELD / BUTTON
<div>
    <input
        type="text"
        bind:value={input_value}
        placeholder="Enter string for API call"
    />
    <button onclick={callAPI}>Call API</button>
</div> -->

<div>
    <!-- Input Field and Button -->
    <div class="input-group">
        <input
            type="text"
            bind:value={input_value}
            placeholder="Enter title for API call"
        />
        <button onclick={callAPI} disabled={is_loading}>
            {#if is_loading}
                Loading...
            {:else}
                Call API
            {/if}
        </button>
    </div>

    <!-- Display API Response -->
    {#if api_response}
        <div>
            <h2>API Response:</h2>
            <pre>{JSON.stringify(api_response, null, 2)}</pre>
        </div>
    {/if}


    <!-- Display Error Message -->
    {#if error}
        <div class="error">
            <p>{error}</p>
        </div>
    {/if}
</div>
