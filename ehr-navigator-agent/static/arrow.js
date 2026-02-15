const {useEffect, useRef} = React;

function ArrowFlow({direction = 'rtl', reverseFlow = false}) {
  const stemPathRef = useRef(null);
  const circlePathRef = useRef(null);
  const arrowRef = useRef(null);
  const circleRefs = useRef([]);
  circleRefs.current = [];

  const circleRadii = [4, 14, 7, 16, 9];

  const stemPaths = {
    'rtl': 'M 250,75 L 125,75 A 50 50 0 0 0 75,125 L 75,132',
    'ltr': 'M 0,75 L 125,75 A 50 50 0 0 1 175,125 L 175,132',
  };
  const circlePaths = {
    'rtl': 'M 300,75 L 125,75 A 50 50 0 0 0 75,125 L 75,182',
    'ltr': 'M -50,75 L 125,75 A 50 50 0 0 1 175,125 L 175,182',
  };

  const stemPathD = stemPaths[direction];
  const circlePathD = circlePaths[direction];

  const addToCircleRefs = el => {
    if (el && !circleRefs.current.includes(el)) {
      circleRefs.current.push(el);
    }
  };

  useEffect(() => {
    gsap.registerPlugin(MotionPathPlugin);
    gsap.set(arrowRef.current, {opacity: 0});
    gsap.set(circleRefs.current, {opacity: 0});

    const len = stemPathRef.current.getTotalLength();
    let pathTween, arrowTween, circlesTl;

    if (reverseFlow) {
      gsap.set(
          stemPathRef.current, {strokeDasharray: len, strokeDashoffset: -len});
      pathTween = gsap.to(
          stemPathRef.current,
          {strokeDashoffset: 0, duration: 1.6, delay: 0, ease: 'power1.inOut'});
    } else {
      gsap.set(
          stemPathRef.current, {strokeDasharray: len, strokeDashoffset: len});
      pathTween = gsap.to(
          stemPathRef.current,
          {strokeDashoffset: 0, duration: 1.6, delay: 0, ease: 'power1.inOut'});
    }

    const motionPathConfig = {
      path: stemPathRef.current,
      align: stemPathRef.current,
      alignOrigin: [0.5, 0.5],
      autoRotate: true,
      start: reverseFlow ? 1 : 0,
      end: reverseFlow ? 0 : 1,
    };

    arrowTween = gsap.to(arrowRef.current, {
      opacity: 1,
      duration: 1.6,
      delay: 0,
      motionPath: motionPathConfig,
      ease: 'power1.inOut',
    });

    const circleMotionPathConfig = {
      path: circlePathRef.current,
      align: circlePathRef.current,
      alignOrigin: [0.5, 0.5],
      start: reverseFlow ? 1 : 0,
      end: reverseFlow ? 0 : 1,
    };

    circlesTl = gsap.timeline({delay: 0});
    circleRefs.current.forEach((circle, index) => {
      circlesTl.fromTo(
          circle, {opacity: 0}, {opacity: 1, duration: 0.2},
          index * 0.3);  // stagger start time
      circlesTl.to(
          circle, {
            motionPath: circleMotionPathConfig,
            duration: 1.6,
            ease: 'power1.inOut',
          },
          index * 0.3);  // same start time as opacity fade in
      circlesTl.to(
          circle, {opacity: 0, duration: 0.2},
          index * 0.3 + 1.4);  // fade out before end
    });
    circlesTl.to(arrowRef.current, {opacity: 0, duration: 0.2}, 2.8);
    circlesTl.to(stemPathRef.current, {opacity: 0, duration: 0.2}, 2.8);

    return () => {
      pathTween.kill();
      arrowTween.kill();
      circlesTl.kill();
    }
  }, [direction, reverseFlow]);

    return (
        <div>
            <svg width='250px' height='150px' viewBox='0 0 250 150' version='1.1' style={{
    overflow: 'visible' }}>
                <defs>
                    <filter id='glow' x='-100%' y='-100%' width='300%' height='300%'>
                        <feGaussianBlur in='SourceAlpha' stdDeviation='3' result='blur'/>
                        <feFlood floodColor='#4285F4' floodOpacity='1' result='color'/>
                        <feComposite in='color' in2='blur' operator='in' result='glow'/>
                        <feMerge>
                            <feMergeNode in='glow'/>
                            <feMergeNode in='SourceGraphic'/>
                        </feMerge>
                    </filter>
                </defs>
                <g id="Page-1" stroke="none" strokeWidth="1" fill="none" fillRule="evenodd">
                    <path ref={stemPathRef} id="Path-1" className="path" fill="none" stroke="#484135" strokeWidth="8" strokeLinejoin="round" strokeMiterlimit="10" d={stemPathD} />
                    <path ref={circlePathRef} id='Path-Circles' stroke='none' d={
    circlePathD} />
                    {[...Array(5)].map((_, i) => (
                        <circle key={i} ref={addToCircleRefs} r={circleRadii[i]} fill="#4285F4" filter="url(#glow)" />
                    ))
}
<polyline ref = {arrowRef} id = 'arrow' points = '0,-9 18,0 0,9 5,0' fill =
     '#484135' /></g>
            </svg>< /div>
    );
}
