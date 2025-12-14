import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const HardyPMFApp = () => {
  const [p, setP] = useState(0.4);
  const [q, setQ] = useState(0.1);
  const [startState, setStartState] = useState(0);
  const [nMax, setNMax] = useState(15);

  const hardyFinishPMF = (parM, i, j, pGood, qBad, maxN = 19) => {
    if (pGood < 0 || qBad < 0 || pGood + qBad >= 1) {
      return { nArray: [], pmf: [] };
    }

    const pOrd = 1 - pGood - qBad;
    const nArray = Array.from({ length: maxN + 1 }, (_, i) => i);
    const pmf = new Array(maxN + 1).fill(0);

    const ordinaryAbs = parM;
    const exceptionalAbs = parM + 1;
    const otherAbs = j === exceptionalAbs ? ordinaryAbs : exceptionalAbs;

    if (i === j) {
      pmf[0] = 1.0;
      return { nArray, pmf };
    }

    if (i === otherAbs) {
      return { nArray, pmf };
    }

    const pState = new Array(parM).fill(0);
    if (i >= 0 && i <= parM - 1) {
      pState[i] = 1.0;
    } else {
      return { nArray, pmf };
    }

    for (let shot = 1; shot <= maxN; shot++) {
      const pNext = new Array(parM).fill(0);

      for (let s = 0; s < parM; s++) {
        const probHere = pState[s];
        if (probHere === 0.0) continue;

        // Good shot: +2
        let newVal = s + 2;
        if (newVal >= exceptionalAbs) {
          if (j === exceptionalAbs) pmf[shot] += probHere * pGood;
        } else if (newVal === ordinaryAbs) {
          if (j === ordinaryAbs) pmf[shot] += probHere * pGood;
        } else {
          pNext[newVal] += probHere * pGood;
        }

        // Ordinary shot: +1
        newVal = s + 1;
        if (newVal >= exceptionalAbs) {
          if (j === exceptionalAbs) pmf[shot] += probHere * pOrd;
        } else if (newVal === ordinaryAbs) {
          if (j === ordinaryAbs) pmf[shot] += probHere * pOrd;
        } else {
          pNext[newVal] += probHere * pOrd;
        }

        // Bad shot: +0
        pNext[s] += probHere * qBad;
      }

      for (let s = 0; s < parM; s++) {
        pState[s] = pNext[s];
      }
    }

    return { nArray, pmf };
  };

  const distributions = useMemo(() => {
    const pars = [3, 4, 5];
    return pars.map(parM => {
      const { nArray, pmf } = hardyFinishPMF(parM, startState, parM, p, q, nMax);
      const meanShots = nArray.reduce((sum, n, idx) => sum + n * pmf[idx], 0);
      const totalProb = pmf.reduce((sum, prob) => sum + prob, 0);

      return {
        parM,
        nArray,
        pmf,
        meanShots,
        totalProb
      };
    });
  }, [p, q, startState, nMax]);

  const chartData = useMemo(() => {
    const maxLength = Math.max(...distributions.map(d => d.nArray.length));
    return Array.from({ length: Math.min(maxLength, nMax + 1) }, (_, i) => {
      const dataPoint = { shots: i };
      distributions.forEach(d => {
        dataPoint[`Par ${d.parM}`] = d.pmf[i] || 0;
      });
      return dataPoint;
    });
  }, [distributions, nMax]);

  const isValidParams = p >= 0 && q >= 0 && p + q < 1;

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-2 text-gray-800">
          Hardy Finish PMF Calculator
        </h1>
        <p className="text-center text-gray-600 mb-8">
          First Passage Distribution to Par for Golf Holes
        </p>

        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Parameters</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Good Shot Prob (p): {p.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="0.9"
                step="0.01"
                value={p}
                onChange={(e) => setP(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">Value +2</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Bad Shot Prob (q): {q.toFixed(2)}
              </label>
              <input
                type="range"
                min="0"
                max="0.9"
                step="0.01"
                value={q}
                onChange={(e) => setQ(parseFloat(e.target.value))}
                className="w-full"
              />
              <p className="text-xs text-gray-500 mt-1">Value +0</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Starting State: {startState}
              </label>
              <input
                type="range"
                min="0"
                max="5"
                step="1"
                value={startState}
                onChange={(e) => setStartState(parseInt(e.target.value))}
                className="w-full"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Shots: {nMax}
              </label>
              <input
                type="range"
                min="5"
                max="25"
                step="1"
                value={nMax}
                onChange={(e) => setNMax(parseInt(e.target.value))}
                className="w-full"
              />
            </div>
          </div>

          <div className="mt-4 p-3 bg-blue-50 rounded">
            <p className="text-sm text-gray-700">
              <strong>Ordinary Shot Prob:</strong> {(1 - p - q).toFixed(2)} (Value +1)
            </p>
            {!isValidParams && (
              <p className="text-sm text-red-600 mt-2">
                ⚠️ Invalid parameters: p + q must be less than 1
              </p>
            )}
          </div>
        </div>

        {isValidParams && (
          <>
            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-xl font-semibold mb-4 text-gray-700">Combined Distribution</h2>
              <ResponsiveContainer width="100%" height={400}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="shots" label={{ value: 'Number of Shots', position: 'insideBottom', offset: -5 }} />
                  <YAxis label={{ value: 'Probability', angle: -90, position: 'insideLeft' }} />
                  <Tooltip formatter={(value) => value.toFixed(4)} />
                  <Legend />
                  <Bar dataKey="Par 3" fill="#2E86AB" />
                  <Bar dataKey="Par 4" fill="#A23B72" />
                  <Bar dataKey="Par 5" fill="#F18F01" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {distributions.map((dist, idx) => {
                const colors = ['#2E86AB', '#A23B72', '#F18F01'];
                const individualData = dist.nArray.slice(0, nMax + 1).map((n, i) => ({
                  shots: n,
                  probability: dist.pmf[i] || 0
                }));

                return (
                  <div key={dist.parM} className="bg-white rounded-lg shadow-lg p-6">
                    <h3 className="text-lg font-semibold mb-2" style={{ color: colors[idx] }}>
                      Par {dist.parM} Hole
                    </h3>
                    <div className="mb-4 p-3 bg-gray-50 rounded">
                      <p className="text-sm"><strong>Mean Shots:</strong> {dist.meanShots.toFixed(2)}</p>
                      <p className="text-sm"><strong>P(reach par):</strong> {dist.totalProb.toFixed(4)}</p>
                    </div>
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={individualData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="shots" />
                        <YAxis />
                        <Tooltip formatter={(value) => value.toFixed(4)} />
                        <Bar dataKey="probability" fill={colors[idx]} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default HardyPMFApp;
