<script>
  import { onMount } from 'svelte';
  let imageFile;
  let textInput = '';
  let generatedImageUrl = '';

  const handleSubmit = async () => {
    const formData = new FormData();
    formData.append('image', imageFile);
    formData.append('text', textInput);

    const response = await fetch('http://localhost:8000/generate', {
      method: 'POST',
      body: formData
    });

    const blob = await response.blob();
    generatedImageUrl = URL.createObjectURL(blob);
  };
</script>

<input type="file" accept="image/*" on:change="{e => imageFile = e.target.files[0]}" />
<input type="text" bind:value="{textInput}" placeholder="Enter text" />
<button on:click="{handleSubmit}">Generate Image</button>

{#if generatedImageUrl}
  <img src="{generatedImageUrl}" alt="Generated Image" />
{/if}

