<!-- src/routes/api_call.svelte -->

<h1>Image API Demo</h1>


<!-- API SCRIPTS -->
<script lang="ts">
    // auxiliaries
    let input_value = $state('');
    interface ApiResponse {
        title: string;
        url: string;
    }
    let api_response: ApiResponse | null = $state(null);
    let error = $state('');
    let is_loading = $state(false);

    // simple hash (not sure if this works): 
    function hashStringToId(str: string, max: number) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash += str.charCodeAt(i);
        }
        return (hash % max) + 1; // ensures ID is between 1 and max
    }

    async function callAPI() {
        if (!input_value.trim()) {
            alert("Please enter a valid title.");
            return;
        }

        is_loading = true;
        error = '';
        api_response = null;

        try {
            // hash input to get photo id
            const photoId = hashStringToId(input_value, 5000);

            let response = await fetch(`https://jsonplaceholder.typicode.com/photos/${photoId}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json; charset=UTF-8',
                }
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


<!-- INPUT FIELD / BUTTON -->
<div>
    <input bind:value={input_value} placeholder="Enter (hash) title" />
    <button onclick={callAPI} disabled={is_loading}>Fetch Image</button>
</div>

<!-- DISPLAY RESULTS -->
{#if is_loading}
    <p>Loading...</p>
{:else if error}
    <p>Error: {error}</p>
{:else if api_response}
    <div>
        <h2>{api_response.title}</h2>
         <!-- (loads image when gateway doesn't time out) -->
        <img src={api_response.url} alt={"timed out fetching " + api_response.url} />
    </div>
{/if}