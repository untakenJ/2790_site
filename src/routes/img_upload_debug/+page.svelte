<script>
    let file; // To store the selected file
    let imageUrl = ""; // To store the uploaded image URL
    let loading = false; // To track loading state
  
    // Your ImgBB API key
    const imgbbApiKey = "84149c1ac4b8219ce0dd0a2068b56e82"; // Replace with your actual ImgBB API key
  
    // Function to handle image upload
    async function uploadImage() {
      if (!file) {
        alert("Please select an image to upload.");
        return;
      }
  
      loading = true;
  
      try {
        const formData = new FormData();
        formData.append("key", imgbbApiKey); // Add API key to formData
        formData.append("image", file); // Add image file to formData
  
        const response = await fetch("https://api.imgbb.com/1/upload", {
          method: "POST",
          body: formData,
        });
  
        const data = await response.json();
  
        if (response.ok) {
          imageUrl = data.data.url; // ImgBB provides the URL in `data.url`
        } else {
          throw new Error(data.error.message || "Failed to upload image");
        }
      } catch (error) {
        alert(`Error: ${error.message}`);
      } finally {
        loading = false;
      }
    }
  
    function handleFileChange(event) {
      file = event.target.files[0];
    }
  </script>
  
  <style>
    .image-preview {
      max-width: 100%;
      max-height: 300px;
      margin-top: 10px;
      border: 1px solid #ccc;
      border-radius: 5px;
    }
  </style>
  
  <div>
    <h2>ImgBB Image Uploader</h2>
    <input type="file" accept="image/*" on:change={handleFileChange} />
    <button on:click={uploadImage} disabled={loading}>
      {loading ? "Uploading..." : "Upload"}
    </button>
  
    {#if imageUrl}
      <h3>Uploaded Image:</h3>
      <img src={imageUrl} alt="Uploaded Image" class="image-preview" />
      <p><strong>URL:</strong> <a href={imageUrl} target="_blank">{imageUrl}</a></p>
    {/if}
  </div>
  