// Get CPU% info stored in file
fetch('cpu.res')
      .then(response => {
        if (!response.ok) {
          throw new Error('Error while loading cpu info');
        }
        return response.text();
      })
      .then(data => {
        const fileContent = data;

	// Attach CPU % to document div
        document.getElementById('cpures').innerText += fileContent;
      })
      .catch(error => {
        console.error('Error while fetching the file: ', error);
});

// Get MEM in MiB info stored in file
fetch('mem.res')
      .then(response => {
        if (!response.ok) {
          throw new Error('Error while loading mem info');
        }
        return response.text();
      })
      .then(data => {
        const fileContent = data;
	// Attach MEM in MiB to document div
        document.getElementById('memres').innerText += fileContent;
      })
      .catch(error => {
        console.error('Error while fetching the file:', error);
});


function goToGallery() {
	      window.location.href = 'gallery.html';
	    }
