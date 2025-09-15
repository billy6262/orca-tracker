

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
          <p>
            <strong>GitHub Repository:</strong> <a href="https://github.com/billy6262/orca-tracker" target="_blank" rel="noopener noreferrer" style={{ color: '#0066cc', textDecoration: 'none' }}>https://github.com/billy6262/orca-tracker</a>
          </p>
        </div>

        <div style={{ marginBottom: '30px' }}>
          <h2>Business Vision</h2>
          <p>
            For decades, regulators have faced the issue of prioritizing ecological preservation and marine commerce. Noise pollution has been a key driver of reductions in the orca population across the world. Regulators are often faced with imposing restrictions on commercial mariners to reduce the impact on marine mammal populations. This often faces harsh criticism from the marine industry, as it can impede commerce in the ports where these restrictions are enacted. For coastal ports, commercial marine traffic often comprises a large portion of the local economy, and the growth of these ports is often in jeopardy when faced with restrictions to marine commerce.
          </p>
          <p>
            Currently, most regulators use a simple heat map with concentrations of reports in specific areas to impose seasonal or yearlong restrictions in areas where populations are seen to frequently appear. Simple heat maps don't tend to properly encapsulate the totality of marine mammal behavior. Often restrictions are imposed in areas where populations are not present or do not frequent at that time of day or season. These statistical models fail to provide insight that is significant enough to reduce impacts on marine mammals and often negatively impact marine traffic with little or no benefit.
          </p>
          <p>
            To that end, we have developed a model that will help predict orca movements in real time. Using crowd-sourced live reports, our model can generate predictions for the next 48 hours. This information can potentially be used by professional mariners to reduce speed in areas with a high probability of presence. By targeting the areas where we place restrictions around marine mammals, we can reduce the impact of both commercial mariners and marine mammals. This will potentially solve the problem of large area blanket restrictions impeding marine commerce at times when there is little to no benefit to marine mammals.
          </p>
          <p>
            Our hope is that this can be another tool for both regulators and commercial mariners in the pursuit of conservation efforts. The targeted application of real-time data can have a profound impact on conservation. Our mission is to tailor the service we offer to have the best possible outcome for not only conservation but maritime commerce as well.
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
