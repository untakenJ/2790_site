<!-- src/lib/components/ApiResponse.svelte -->

<script>
    export let apiResponse;
</script>

<style>
    .response {
        background-color: #f1f1f1;
        padding: 1rem;
        border-radius: 5px;
        margin-top: 1rem;
    }
    pre {
        white-space: pre-wrap;
        word-wrap: break-word;
    }
</style>

<div class="response">
    <h2>API Response:</h2>
    <pre>{JSON.stringify(apiResponse, null, 2)}</pre>
</div>

