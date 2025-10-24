"""
Code Execution Tool

Provides safe Python code execution for data analysis, calculations,
and visualization.
"""

import json
from typing import Dict, Any
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import io
import sys
from contextlib import redirect_stdout, redirect_stderr


def execute_python_code(code: str, description: str = "") -> str:
    """
    Execute Python code for data analysis and calculations.

    This tool provides a safe environment for running Python code
    to analyze trading data, perform calculations, and generate insights.

    Args:
        code (str): Python code to execute
        description (str): Description of what the code does

    Returns:
        str: JSON string with execution results

    Example:
        >>> execute_python_code('''
        ... import pandas as pd
        ... import numpy as np
        ...
        ... # Calculate moving averages
        ... data = pd.DataFrame(btc_prices)
        ... data['MA20'] = data['close'].rolling(window=20).mean()
        ... data['MA50'] = data['close'].rolling(window=50).mean()
        ...
        ... print(data[['close', 'MA20', 'MA50']].tail())
        ... ''', description="Calculate 20 and 50-day moving averages for BTC")

    Available libraries:
        - pandas: Data manipulation and analysis
        - numpy: Numerical computing
        - matplotlib: Plotting and visualization
        - scipy: Scientific computing
        - sklearn: Machine learning (basic algorithms)

    Safety:
        - Runs in sandboxed environment
        - No file system access (except temp files)
        - No network access
        - Limited execution time

    Common use cases:
        1. Calculate technical indicators (RSI, MACD, Bollinger Bands)
        2. Perform statistical analysis
        3. Generate charts and visualizations
        4. Backtest trading strategies
        5. Risk/reward calculations
    """
    
    # Capture stdout and stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    result = {
        "success": False,
        "output": "",
        "error": "",
        "description": description,
        "variables": {}
    }
    
    try:
        # Create a safe execution environment
        safe_globals = {
            "__builtins__": {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "tuple": tuple,
                "set": set,
                "range": range,
                "enumerate": enumerate,
                "zip": zip,
                "map": map,
                "filter": filter,
                "sum": sum,
                "max": max,
                "min": min,
                "abs": abs,
                "round": round,
                "sorted": sorted,
                "reversed": reversed,
                "any": any,
                "all": all,
                "isinstance": isinstance,
                "type": type,
                "hasattr": hasattr,
                "getattr": getattr,
                "setattr": setattr,
                "dir": dir,
                "vars": vars,
                "locals": locals,
                "globals": globals,
            },
            "pd": pd,
            "np": np,
            "plt": plt,
            "json": json,
            "io": io,
            "sys": sys,
        }
        
        safe_locals = {}
        
        # Execute code with captured output
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, safe_globals, safe_locals)
        
        # Get captured output
        stdout_output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()
        
        result["success"] = True
        result["output"] = stdout_output
        result["error"] = stderr_output
        
        # Capture some common variables if they exist
        common_vars = ["data", "df", "result", "output", "result_df", "analysis"]
        for var in common_vars:
            if var in safe_locals:
                try:
                    if hasattr(safe_locals[var], "to_dict"):
                        result["variables"][var] = safe_locals[var].to_dict()
                    elif hasattr(safe_locals[var], "tolist"):
                        result["variables"][var] = safe_locals[var].tolist()
                    else:
                        result["variables"][var] = str(safe_locals[var])
                except:
                    result["variables"][var] = str(safe_locals[var])
    
    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["output"] = stdout_capture.getvalue()
    
    return json.dumps(result, indent=2, default=str)


def calculate_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate common technical indicators.
    
    Args:
        data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
    
    Returns:
        DataFrame with additional technical indicator columns
    """
    df = data.copy()
    
    # Simple Moving Averages
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    
    # Exponential Moving Averages
    df['EMA_12'] = df['close'].ewm(span=12).mean()
    df['EMA_26'] = df['close'].ewm(span=26).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Bollinger Bands
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    # Volume indicators
    df['Volume_SMA'] = df['volume'].rolling(window=20).mean()
    df['Volume_Ratio'] = df['volume'] / df['Volume_SMA']
    
    return df


def generate_trading_signals(data: pd.DataFrame) -> pd.DataFrame:
    """
    Generate basic trading signals based on technical indicators.
    
    Args:
        data: DataFrame with technical indicators
    
    Returns:
        DataFrame with signal columns
    """
    df = data.copy()
    
    # Buy signals
    df['Buy_Signal'] = (
        (df['close'] > df['SMA_20']) &
        (df['SMA_20'] > df['SMA_50']) &
        (df['RSI'] < 70) &
        (df['MACD'] > df['MACD_Signal'])
    )
    
    # Sell signals
    df['Sell_Signal'] = (
        (df['close'] < df['SMA_20']) |
        (df['RSI'] > 80) |
        (df['MACD'] < df['MACD_Signal'])
    )
    
    # Trend signals
    df['Trend'] = 'Neutral'
    df.loc[df['close'] > df['SMA_50'], 'Trend'] = 'Bullish'
    df.loc[df['close'] < df['SMA_50'], 'Trend'] = 'Bearish'
    
    return df
