<script>
	let { children } = $props();
</script>

<nav>
    <p><a href = './'>Home</a></p>
    <p><a href="./image_api_call">Image API Call Demo</a></p>
    <p><a href="./image_interaction">Image Interaction</a></p>
    <p><a href="./paint_interaction">Paint Interaction</a></p>
    <p><a href="./further_painting">Experimental Painting Functions</a></p>
</nav>

{@render children()}
