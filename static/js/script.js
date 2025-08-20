// static/js/script.js
document.addEventListener('DOMContentLoaded', function() {
    const resumeForm = document.getElementById('resume-form');
    const resumeUpload = document.getElementById('resume-upload');
    const fileName = document.getElementById('file-name');
    const analyzeBtn = document.getElementById('analyze-btn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    const wordCount = document.getElementById('word-count');
    const lengthWarning = document.getElementById('length-warning');
    const lengthMessage = document.getElementById('length-message');
    const sectionsList = document.getElementById('sections-list');
    const skillsContainer = document.getElementById('skills-container');
    const recommendationsList = document.getElementById('recommendations-list');
    const newAnalysisBtn = document.getElementById('new-analysis');
    
    // File selection event
    resumeUpload.addEventListener('change', function() {
        if (this.files && this.files[0]) {
            fileName.textContent = this.files[0].name;
            // Enable the analyze button when a file is selected
            analyzeBtn.disabled = false;
        } else {
            fileName.textContent = 'No file selected';
            analyzeBtn.disabled = true;
        }
    });
    
    // Initially disable the analyze button
    analyzeBtn.disabled = true;
    
    // File upload and drag-drop area
    const fileUpload = document.querySelector('.file-upload');
    
    fileUpload.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = '#4caf50';
        this.style.backgroundColor = 'rgba(76, 175, 80, 0.05)';
    });
    
    fileUpload.addEventListener('dragleave', function() {
        this.style.borderColor = '';
        this.style.backgroundColor = '';
    });
    
    fileUpload.addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = '';
        this.style.backgroundColor = '';
        
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            resumeUpload.files = e.dataTransfer.files;
            fileName.textContent = e.dataTransfer.files[0].name;
            // Enable the analyze button when a file is dropped
            analyzeBtn.disabled = false;
        }
    });
    
    // Form submission
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Check if a file is selected
        if (!resumeUpload.files || !resumeUpload.files[0]) {
            alert('Please select a file to upload.');
            return;
        }
        
        // Check file extension
        const file = resumeUpload.files[0];
        const extension = file.name.split('.').pop().toLowerCase();
        
        if (extension !== 'pdf' && extension !== 'docx') {
            alert('Only PDF and DOCX files are supported.');
            return;
        }
        
        // Show loading
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        
        // Create FormData object
        const formData = new FormData();
        formData.append('resume', file);
        
        // Send to server
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.error || 'Unknown error occurred');
                });
            }
            return response.json();
        })
        .then(data => {
            // Hide loading and show results
            loadingDiv.classList.add('hidden');
            resultsDiv.classList.remove('hidden');
            
            // Display analysis results
            displayResults(data);
        })
        .catch(error => {
            loadingDiv.classList.add('hidden');
            alert(error.message || 'An error occurred during analysis.');
        });
    });
    
    // Make the entire file upload area clickable
    fileUpload.addEventListener('click', function(e) {
        resumeUpload.click();
    });
    
    // Function to display analysis results
    function displayResults(data) {
        // Word count
        wordCount.textContent = data.word_count;
        
        // Length warning
        if (data.is_too_short || data.is_too_long) {
            lengthWarning.classList.remove('hidden');
            lengthMessage.textContent = data.is_too_short ? 
                'Your resume is too short. Consider adding more details.' : 
                'Your resume is quite long. Consider making it more concise.';
        } else {
            lengthWarning.classList.add('hidden');
        }
        
        // Sections found
        sectionsList.innerHTML = '';
        const sectionNames = {
            'contact': 'Contact Information',
            'education': 'Education',
            'experience': 'Work Experience',
            'skills': 'Skills',
            'projects': 'Projects',
            'achievements': 'Achievements',
            'summary': 'Professional Summary'
        };
        
        for (const [section, name] of Object.entries(sectionNames)) {
            const found = data.sections_found[section];
            
            const div = document.createElement('div');
            div.className = `checkbox-item ${found ? '' : 'missing'}`;
            
            div.innerHTML = `
                <i class="fas fa-${found ? 'check' : 'times'}"></i>
                <span>${name}</span>
            `;
            
            sectionsList.appendChild(div);
        }
        
        // Skills found
        skillsContainer.innerHTML = '';
        if (data.skills_found && data.skills_found.length > 0) {
            data.skills_found.forEach(skill => {
                const skillTag = document.createElement('span');
                skillTag.className = 'skill-tag';
                skillTag.textContent = skill;
                skillsContainer.appendChild(skillTag);
            });
        } else {
            skillsContainer.innerHTML = '<p>No specific skills identified. Consider adding more technical or industry-specific skills.</p>';
        }
        
        // Recommendations
        recommendationsList.innerHTML = '';
        if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(recommendation => {
                const li = document.createElement('li');
                li.textContent = recommendation;
                recommendationsList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'Your resume looks good! Consider tailoring it to specific job descriptions.';
            recommendationsList.appendChild(li);
        }
    }
    
    // New analysis button
    newAnalysisBtn.addEventListener('click', function() {
        resultsDiv.classList.add('hidden');
        resumeForm.reset();
        fileName.textContent = 'No file selected';
        analyzeBtn.disabled = true;
    });
});