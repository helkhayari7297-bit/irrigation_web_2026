let currentStep = 1;

function goToStep(step) {
    document.querySelectorAll('.step-panel').forEach((p, i) => {
        p.classList.toggle('active', i === step - 1);
    });
    document.querySelectorAll('.step-num').forEach((n, i) => {
        n.classList.toggle('active', i === step - 1);
        n.classList.toggle('done', i < step - 1);
    });
    currentStep = step;
}

function nextStep(step) {
    if (step < 3) goToStep(step + 1);
}