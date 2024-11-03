<script>
	let { children } = $props();
</script>

<nav>
    <p><a href = './'>Home</a></p>
    <p><a href="./base_api_call">Base API Call Demo</a></p>
    <p><a href="./image_api_call">Image API Call Demo</a></p>
</nav>

{@render children()}
