let roiChartInstance = null;

document.getElementById('calculator-form').addEventListener('submit', function(e) {
    e.preventDefault();
    calculateDeal();
});

function calculateDeal() {
    // 1. Get inputs
    const price = parseFloat(document.getElementById('price').value);
    const downPayment = parseFloat(document.getElementById('down-payment').value);
    const interestRate = parseFloat(document.getElementById('interest-rate').value) / 100;
    const loanTerm = parseFloat(document.getElementById('loan-term').value);

    const monthlyRent = parseFloat(document.getElementById('monthly-rent').value);

    const propertyTax = parseFloat(document.getElementById('property-tax').value);
    const insurance = parseFloat(document.getElementById('insurance').value);
    const maintenance = parseFloat(document.getElementById('maintenance').value);

    // 2. Loan Calculations
    const loanAmount = price - downPayment;
    const monthlyInterestRate = interestRate / 12;
    const totalPayments = loanTerm * 12;

    let monthlyMortgage = 0;
    if (interestRate > 0) {
        monthlyMortgage = loanAmount * (monthlyInterestRate * Math.pow(1 + monthlyInterestRate, totalPayments)) / (Math.pow(1 + monthlyInterestRate, totalPayments) - 1);
    } else {
        monthlyMortgage = loanAmount / totalPayments;
    }

    // 3. Operating Expenses & NOI
    const monthlyOperatingExpenses = propertyTax + insurance + maintenance;
    const totalMonthlyExpenses = monthlyOperatingExpenses + monthlyMortgage;
    const monthlyNOI = monthlyRent - monthlyOperatingExpenses;
    const yearlyNOI = monthlyNOI * 12;

    // 4. Cash Flow & Returns
    const monthlyCashFlow = monthlyRent - totalMonthlyExpenses;
    const yearlyCashFlow = monthlyCashFlow * 12;

    const capRate = (yearlyNOI / price) * 100;

    // Cash on Cash Return: Yearly Cash Flow / Total Cash Invested (Down Payment)
    let cocReturn = 0;
    if (downPayment > 0) {
        cocReturn = (yearlyCashFlow / downPayment) * 100;
    } else {
        // If 0% down, CoC is practically infinite if positive cash flow
        cocReturn = yearlyCashFlow > 0 ? Infinity : -Infinity;
    }

    // 5. Update UI
    document.getElementById('res-cash-flow').innerText = `$${monthlyCashFlow.toFixed(2)}`;
    document.getElementById('res-cash-flow').className = monthlyCashFlow >= 0 ? "text-success" : "text-danger";

    if (cocReturn === Infinity) {
        document.getElementById('res-coc').innerText = "Infinite";
    } else {
        document.getElementById('res-coc').innerText = `${cocReturn.toFixed(2)}%`;
    }
    document.getElementById('res-coc').className = cocReturn >= 8 ? "text-success" : (cocReturn > 0 ? "text-warning" : "text-danger");

    document.getElementById('res-noi').innerText = `$${yearlyNOI.toFixed(2)}`;
    document.getElementById('res-cap-rate').innerText = `${capRate.toFixed(2)}%`;

    // 6. Verdict
    const verdictContainer = document.getElementById('verdict-container');
    const verdictTitle = document.getElementById('verdict-title');
    const verdictText = document.getElementById('verdict-text');

    verdictContainer.classList.remove('d-none', 'alert-success', 'alert-warning', 'alert-danger', 'alert-info');

    let breakEvenYears = downPayment > 0 && yearlyCashFlow > 0 ? (downPayment / yearlyCashFlow).toFixed(1) : null;

    if (monthlyCashFlow < 0) {
        verdictContainer.classList.add('alert-danger');
        verdictTitle.innerText = "Not Recommended";
        verdictText.innerText = "This property generates negative cash flow. You will be losing money every month.";
    } else if (cocReturn < 5) {
        verdictContainer.classList.add('alert-warning');
        verdictTitle.innerText = "Marginal Investment";
        verdictText.innerText = `Positive cash flow, but Cash-on-Cash return is low. It will take ${breakEvenYears} years to recover your down payment.`;
    } else {
        verdictContainer.classList.add('alert-success');
        verdictTitle.innerText = "Good Investment!";
        verdictText.innerText = `Solid positive cash flow and good Cash-on-Cash return. It will take ${breakEvenYears} years to recover your down payment.`;
    }

    // 7. Render Graph
    renderChart(loanAmount, monthlyInterestRate, monthlyMortgage, totalPayments, downPayment, yearlyCashFlow, loanTerm);
}

function renderChart(loanAmount, monthlyInterestRate, monthlyMortgage, totalPayments, downPayment, yearlyCashFlow, loanTerm) {
    const years = [];
    const cumulativeCashFlow = [];
    const equityBuildUp = [];

    let currentBalance = loanAmount;
    let accumulatedCash = -downPayment; // Start with negative (the investment)

    for (let year = 0; year <= loanTerm; year++) {
        years.push(`Year ${year}`);

        if (year === 0) {
            cumulativeCashFlow.push(accumulatedCash);
            equityBuildUp.push(downPayment);
        } else {
            // Add a year of cash flow
            accumulatedCash += yearlyCashFlow;
            cumulativeCashFlow.push(accumulatedCash);

            // Calculate 12 months of mortgage amortization
            for(let m = 0; m < 12; m++) {
                let interestPayment = currentBalance * monthlyInterestRate;
                let principalPayment = monthlyMortgage - interestPayment;
                currentBalance -= principalPayment;
                if(currentBalance < 0) currentBalance = 0;
            }
            let currentEquity = (loanAmount + downPayment) - currentBalance;
            equityBuildUp.push(currentEquity);
        }
    }

    const ctx = document.getElementById('roiChart').getContext('2d');

    if (roiChartInstance) {
        roiChartInstance.destroy();
    }

    roiChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [
                {
                    label: 'Cumulative Cash Flow ($)',
                    data: cumulativeCashFlow,
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                },
                {
                    label: 'Equity Built ($)',
                    data: equityBuildUp,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return '$' + value.toLocaleString();
                        }
                    }
                }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(context.parsed.y);
                            }
                            return label;
                        }
                    }
                }
            }
        }
    });
}

// Initial calculation
calculateDeal();
