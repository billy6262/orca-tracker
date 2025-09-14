

const AboutPage = () => {
  return (
    <div className="about-page" style={{ minHeight: '100vh', backgroundColor: '#f5f5f5', padding: '20px' }}>
      <div style={{ 
        maxWidth: '800px', 
        margin: '0 auto', 
        backgroundColor: 'white', 
        padding: '40px', 
        borderRadius: '8px', 
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)', 
        lineHeight: '1.6' 
      }}>
        <h1>Contact</h1>
        
        <div style={{ marginBottom: '30px' }}>
          <h2>About the Developer</h2>
          <p>
            Hi! I'm Andrew Dorchak, and I'm currently serving in the United States Coast Guard while finishing my Bachelor's degree in Computer Science. This Orca Tracker application represents my capstone project, born from my deep interest in the marine industry and marine mammal conservation.
          </p>
          <p>
            As someone who works in the maritime environment daily, I've developed a passion for leveraging technology to support marine conservation efforts. This project combines my technical skills with my professional maritime experience to create a practical tool for predicting orca movements in the Puget Sound.
          </p>
          <p>
            The intersection of my Coast Guard service, computer science education, and love for marine conservation has inspired me to explore how machine learning and data analysis can contribute to protecting our marine ecosystems while supporting maritime commerce.
          </p>
        </div>

        <div style={{ marginBottom: '30px' }}>
          <h2>Professional Inquiries</h2>
          <p>
            For professional inquiries, collaboration opportunities, or questions about this project, please feel free to reach out:
          </p>
          <p>
            <strong>Email:</strong> <a href="mailto:andrew.dorchak98@gmail.com" style={{ color: '#0066cc', textDecoration: 'none' }}>andrew.dorchak98@gmail.com</a>
          </p>
        </div>

        <div style={{ marginBottom: '30px' }}>
          <h2>About This Project</h2>
          <p>
            This Orca Tracker application serves as my Computer Science capstone project, demonstrating the practical application of machine learning techniques in marine mammal conservation. The project showcases:
          </p>
          <ul>
            <li>Advanced data processing and analysis of over 40,000 marine mammal sighting reports</li>
            <li>Implementation of XGBoost machine learning models for predictive analytics</li>
            <li>Full-stack web development with React frontend and Django backend</li>
            <li>Real-world application addressing marine conservation challenges</li>
            <li>Integration of maritime industry knowledge with computer science principles</li>
          </ul>
        </div>

        <div style={{ backgroundColor: '#f8f9fa', padding: '20px', borderRadius: '6px', border: '1px solid #e9ecef' }}>
          <h3 style={{ marginTop: '0', color: '#495057' }}>Current Focus</h3>
          <p style={{ marginBottom: '0', color: '#6c757d' }}>
            I will soon be seeking opportunities to apply my dual expertise in maritime operations and computer science to develop innovative solutions for marine conservation and maritime technology. This project represents my commitment to using technology as a force for environmental protection and maritime safety.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AboutPage;
