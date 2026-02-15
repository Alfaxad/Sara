const {useState, useEffect, useRef, useCallback} = React;

function Markdown({ content }) {
    const md = window.markdownit();
    const html = md.render(content);
    return <div dangerouslySetInnerHTML={{ __html: html }} />;
}

function AgentRunner({onBack}) {
  const [questions, setQuestions] = useState([]);
  const [selectedQuestionId, setSelectedQuestionId] = useState(null);
  const [output, setOutput] = useState([]);
  const [answer, setAnswer] = useState('');
  const [intermediateData, setIntermediateData] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [isFhirFlowReversed, setIsFhirFlowReversed] = useState(false);
  const [isVertexFlowReversed, setIsVertexFlowReversed] = useState(false);
  const [isFhirFlowActive, setIsFhirFlowActive] = useState(false);
  const [isVertexFlowActive, setIsVertexFlowActive] = useState(false);
  const [isVertexWorking, setIsVertexWorking] = useState(false);
  const [showDetailsDialog, setShowDetailsDialog] = useState(false);

  useEffect(() => {
    fetch('/questions').then(response => response.json()).then(data => {
      setQuestions(data);
    });
  }, []);

  const eventQueue = useRef([]);
  const isProcessingQueue = useRef(false);
  const eventSourceRef = useRef(null);
  const timeoutRef = useRef(null);

  const eventIdCounter = useRef(0);
  const addEvent = (eventText) => {
      const event = {id: eventIdCounter.current++, text: eventText};
      setOutput(prevOutput => [event, ...prevOutput]);
  };

  const processMessageQueue = useCallback(() => {
    if (eventQueue.current.length === 0) {
      isProcessingQueue.current = false;
      return;
    }

    isProcessingQueue.current = true;
    const event = eventQueue.current.shift();
    const message = JSON.parse(event.data);
    const timeout = message.destination === 'LLM' && message.request ? 6000 : 3000;

    if (message.destination === 'FHIR') {
      setIsFhirFlowReversed(!message.request);
      setIsFhirFlowActive(true);
      setIsVertexFlowActive(false);
      setIsVertexWorking(false);
    } else if (message.destination === 'LLM') {
      setIsVertexFlowReversed(!message.request);
      setIsVertexFlowActive(true);
      setIsFhirFlowActive(false);
      setIsVertexWorking(message.request);
    } else {
      setIsFhirFlowActive(false);
      setIsVertexFlowActive(false);
      setIsVertexWorking(false);
    }

    if (message.final) {
      addEvent(message.event);
      setAnswer(message.data);
      setIntermediateData('');
      eventSourceRef.current.close();
      setIsRunning(false);
      setIsVertexWorking(false);
      // If queue still has items, process them, otherwise stop.
      if (eventQueue.current.length > 0) {
        timeoutRef.current = setTimeout(processMessageQueue, timeout);
      } else {
        isProcessingQueue.current = false;
        if (timeoutRef.current) clearTimeout(timeoutRef.current);
      }
      return;
    }

    // Not final message
    if (message.data && typeof message.data !== 'string') {
      setIntermediateData(
          '```json\n' + JSON.stringify(message.data, null, 2) + '\n```');
      addEvent(`${message.event}: Received structured data.`);
    } else {
      setIntermediateData(message.data || '');
      let dataSuffix = message.data && message.data.length < 30 ? `: ${message.data}` : '';
      addEvent(`${message.event}${dataSuffix}`);
    }

    timeoutRef.current = setTimeout(processMessageQueue, timeout);
  }, []);

  const runAgent = (questionId) => {
    setSelectedQuestionId(questionId);
    setOutput([]);
    setAnswer('');
    setIntermediateData('');
    setIsRunning(true);
    setIsFhirFlowActive(false);
    setIsVertexFlowActive(false);
    setIsVertexWorking(false);
    eventQueue.current = [];
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    isProcessingQueue.current = false;

    eventSourceRef.current =
        new EventSource(`/run_agent?question_id=${questionId}`);

    eventSourceRef.current.onmessage = event => {
      eventQueue.current.push(event);
      if (!isProcessingQueue.current) {
        processMessageQueue();
      }
    };

    eventSourceRef.current.onerror = () => {
      const hasFinalMessage = eventQueue.current.some(event => JSON.parse(event.data).final);
      if (hasFinalMessage) {
        eventSourceRef.current.close();
        if (!isProcessingQueue.current && eventQueue.current.length > 0) {
          processMessageQueue();
        }
        return;
      }

      addEvent('Error connecting to the agent.');
      eventSourceRef.current.close();
      setIsRunning(false);
      eventQueue.current = [];
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      isProcessingQueue.current = false;
      setIsVertexWorking(false);
    };
  };

    return (
        <div className='agent-page-container'>
            {showDetailsDialog && <Dialog onClose={() => setShowDetailsDialog(false)} />}
            <div className='demo-header'>
                <button className='back-button' onClick={onBack}>&lt; Back</button>
                <button className="details-button" onClick={() => setShowDetailsDialog(true)}>
                    <span className="material-symbols-outlined">
                        code
                    </span>
                    Details about this Demo
                </button>
            </div>
            <div className='demo-frame'>
                <div className='agent-container'>
                    <div className='left-panel'>
                        <h4>Clinician</h4>
                        <img src='static/clinician.avif' alt='Clinician' className='clinician-image' />
                        <h5>Select a Task</h5>
                        <div className="task-list">
                            {questions.map(q => (
                                <button key={q.id}
                                        className={`task-button ${selectedQuestionId === q.id && isRunning ? 'running' : ''}`}
                                        onClick={() => runAgent(q.id)}
                                        disabled={isRunning}>
                                    {q.question}
                                </button>
                            ))}
                        </div>
                    </div>
                    <div className='right-panel'>
                        <div className='agent-header'>
                            EHR Navigator Agent
                        </div>
                        <div className="agent-vertex-arrow">
                            {isVertexFlowActive && <ArrowFlow reverseFlow={isVertexFlowReversed} />}
                        </div>
                        <img src='static/agent.svg' alt='Agent' className='agent agent-image' />
                        <div className='agent-fhir-arrow'>
                            {isFhirFlowActive && <ArrowFlow direction='ltr' reverseFlow={isFhirFlowReversed} />}
                        </div>
                        <div className={`vertex ${isVertexWorking ? 'working' : ''}`}>
                            <div className='gcp-resource-frame'>
                                <img src='static/vertex-ai.svg' alt='Vertex' className='vertex-image' />
                                <img src='static/medgemma.avif' alt='MedGemma'/>
                                <div>(Vertex AI)</div>
                            </div>
                        </div>
                        <div className='event-log'>
                            {output.map((event) => (
                                <div key={event.id} className="event-item">{event.text}</div>
                            ))}
                        </div>
                        <div className='fhir'>
                            
                            <div className="gcp-resource-frame">
                                <img src='static/fhir-colors.svg' alt='FHIR' className='fhir-image' />
                                <div>Electronic Health Record (EHR)</div>
                                <div>(FHIR Store)</div>
                            </div>
                        </div>
                        {isRunning && intermediateData && <div className='answer'>
                            <Markdown content={intermediateData} />
                        </div>}
                        {answer && <div className='answer'>
                            {questions.find(q => q.id === selectedQuestionId)?.question}<br/><br/>
                            <strong>Answer: </strong> <Markdown content={answer} />
                        </div>}
                    </div>
                </div>
            </div>
        </div>
    );
}

function Introduction({ onStart }) {
    return (
        <div className="intro-page">
            <header className="intro-header">
                <img src='static/medgemma.avif' className='logo' />
            </header>
            <main className="intro-content">
                <section className="diagram-section">
                   <img src='static/intro.svg' alt='Agent Diagram' />
                </section>
                <section className="text-section">
                    <h1>EHR Navigator Agent</h1>
                    <p>In a clinical setting, agents are crucial for navigating and utilizing vast Electronic Health Record (EHR) data, often stored in FHIR format. An agent can efficiently answer specific questions or perform tasks related to a patient by intelligently fetching the most relevant information from their potentially very large and complex record.</p>
                    <p>This demo showcases how an agent can use <a href="https://developers.google.com/health-ai-developer-foundations/medgemma" target="_blank">MedGemma’s</a> comprehension of Fast Healthcare Interoperability Resources (FHIR) standard to intelligently navigate patient's health records. The agent first identifies what information is available, then plans how to retrieve the relevant parts. It fetches data in steps, extracting key facts along the way, and finally combines all these facts to provide a complete answer. This is a simplified example to illustrate the process. All patient data in this demo is synthetic, generated by Synthea (github.com/synthetichealth/synthea).</p>
                    <div className='disclaimer'>
                        <p><span className='disclaimer-badge'>Disclaimer</span> This demonstration is for illustrative purposes only and does not represent a finished or approved product. It is not representative of compliance to any regulations or standards for quality, safety or efficacy. Any real-world application would require additional development, training, and adaptation. The experience highlighted in this demo shows MedGemma's baseline capability for the displayed task and is intended to help developers and users explore possible applications and inspire further development.</p>
                    </div>
                    <button onClick={onStart} className="view-demo-button">View Demo</button>
                </section>
            </main>
        </div>
    );
}

function App() {
    const [showIntro, setShowIntro] = useState(true);

    useEffect(() => {
        if(showIntro) {
            document.body.classList.add('intro-active');
        } else {
            document.body.classList.remove('intro-active');
        }
    }, [showIntro]);

    if (showIntro) {
        return <Introduction onStart={() => setShowIntro(false)} />;
}

    return <AgentRunner onBack={() => setShowIntro(true)} />;
}

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
