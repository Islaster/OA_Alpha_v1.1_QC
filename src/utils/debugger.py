"""
Debugging utilities for Bounding Box Minimizer
Mac-compatible version with cross-platform file handling.
"""
import time
import os
import json
from datetime import datetime
from collections import defaultdict
from pathlib import Path


class Debugger:
    def __init__(self, enabled=True, log_file="debug_log.txt", save_intermediate=False, verbose=False):
        """
        Initialize debugger.
        
        Args:
            enabled: Enable/disable debugging
            log_file: Path to debug log file
            save_intermediate: Save intermediate states during optimization
            verbose: Print all debug messages to console
        """
        self.enabled = enabled
        self.log_file = str(Path(log_file).resolve()) if log_file else None
        self.save_intermediate = save_intermediate
        self.verbose = verbose
        self.start_time = time.time()
        self.events = []
        self.performance_stats = defaultdict(list)
        self.step_count = 0
        self.rotation_history = []
        
        if self.enabled and self.log_file:
            try:
                self._init_log()
            except Exception:
                self.log_file = None
    
    def _init_log(self):
        """Initialize log file"""
        # Ensure directory exists
        log_path = Path(self.log_file)
        if log_path.parent != Path('.'):
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write(f"=== Debug Log Started: {datetime.now()} ===\n\n")
    
    def log(self, message, level="INFO"):
        """Log a debug message"""
        if not self.enabled:
            return
        
        timestamp = time.time() - self.start_time
        log_entry = f"[{timestamp:8.2f}s] [{level:5s}] {message}\n"
        
        if self.log_file:
            try:
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except Exception:
                pass
        
        if level != "INFO" or self.verbose:
            print(f"DEBUG [{level}]: {message}")
    
    def log_event(self, event_type, data=None):
        """Log an event with optional data"""
        if not self.enabled:
            return
        
        event = {
            "time": time.time() - self.start_time,
            "type": event_type,
            "data": data or {}
        }
        self.events.append(event)
        self.log(f"Event: {event_type} - {data}")
    
    def log_rotation_attempt(self, rotation_deg, bbox_size, improvement=None):
        """Log a rotation attempt"""
        if not self.enabled:
            return
        
        self.step_count += 1
        attempt = {
            "step": self.step_count,
            "rotation": rotation_deg,
            "bbox_size": bbox_size,
            "improvement": improvement,
            "time": time.time() - self.start_time
        }
        self.rotation_history.append(attempt)
        
        if self.verbose or (improvement and improvement > 1.0):
            if improvement:
                self.log(f"Step {self.step_count}: Rotation {rotation_deg} -> BBox: {bbox_size:.6f} (Improvement: {improvement:.4f}%)")
            else:
                self.log(f"Step {self.step_count}: Rotation {rotation_deg} -> BBox: {bbox_size:.6f}")
        elif self.log_file:
            try:
                timestamp = time.time() - self.start_time
                if improvement:
                    log_entry = f"[{timestamp:8.2f}s] [INFO ] Step {self.step_count}: Rotation {rotation_deg} -> BBox: {bbox_size:.6f} (Improvement: {improvement:.4f}%)\n"
                else:
                    log_entry = f"[{timestamp:8.2f}s] [INFO ] Step {self.step_count}: Rotation {rotation_deg} -> BBox: {bbox_size:.6f}\n"
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except:
                pass
    
    def log_performance(self, operation, duration):
        """Log performance metrics"""
        if not self.enabled:
            return
        
        self.performance_stats[operation].append(duration)
        if self.verbose or duration > 0.1:
            self.log(f"Performance: {operation} took {duration:.3f}s")
        elif self.log_file:
            try:
                timestamp = time.time() - self.start_time
                log_entry = f"[{timestamp:8.2f}s] [PERF ] Performance: {operation} took {duration:.3f}s\n"
                with open(self.log_file, 'a', encoding='utf-8') as f:
                    f.write(log_entry)
            except:
                pass
    
    def save_state(self, obj, filename_prefix="debug_state"):
        """Save intermediate state"""
        if not self.enabled or not self.save_intermediate:
            return
        
        try:
            import bpy
            filename = f"{filename_prefix}_step{self.step_count}.blend"
            bpy.ops.wm.save_as_mainfile(filepath=filename)
            self.log(f"Saved intermediate state: {filename}")
        except Exception as e:
            self.log(f"Failed to save state: {e}", "ERROR")
    
    def get_summary(self):
        """Get debugging summary"""
        if not self.enabled:
            return {}
        
        total_time = time.time() - self.start_time
        
        stats = {
            "total_time": total_time,
            "total_steps": self.step_count,
            "events_count": len(self.events),
            "rotation_history_length": len(self.rotation_history),
            "performance_stats": {}
        }
        
        for operation, durations in self.performance_stats.items():
            if durations:
                stats["performance_stats"][operation] = {
                    "count": len(durations),
                    "total": sum(durations),
                    "average": sum(durations) / len(durations),
                    "min": min(durations),
                    "max": max(durations)
                }
        
        return stats
    
    def save_report(self, output_file="debug_report.json"):
        """Save comprehensive debug report"""
        if not self.enabled:
            return
        
        report = {
            "summary": self.get_summary(),
            "events": self.events,
            "rotation_history": self.rotation_history,
            "performance_stats": dict(self.performance_stats)
        }
        
        output_path = Path(output_file)
        if output_path.parent != Path('.'):
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        self.log(f"Debug report saved to {output_file}")
    
    def print_summary(self):
        """Print debugging summary to console"""
        if not self.enabled:
            return
        
        summary = self.get_summary()
        print("\n" + "="*60)
        print("DEBUG SUMMARY")
        print("="*60)
        print(f"Total time: {summary['total_time']:.2f}s")
        print(f"Total steps: {summary['total_steps']}")
        print(f"Events logged: {summary['events_count']}")
        print(f"\nPerformance Stats:")
        for op, stats in summary.get('performance_stats', {}).items():
            print(f"  {op}:")
            print(f"    Count: {stats['count']}")
            print(f"    Avg: {stats['average']:.3f}s")
            print(f"    Min: {stats['min']:.3f}s")
            print(f"    Max: {stats['max']:.3f}s")
        print("="*60)
    
    def checkpoint(self, name):
        """Create a checkpoint with timing"""
        if not self.enabled:
            return
        
        elapsed = time.time() - self.start_time
        self.log(f"Checkpoint: {name} (elapsed: {elapsed:.2f}s)")
        self.log_event("checkpoint", {"name": name, "elapsed": elapsed})


# Global debugger instance
_debugger = None

def get_debugger(enabled=True, **kwargs):
    """Get or create global debugger instance"""
    global _debugger
    if _debugger is None:
        _debugger = Debugger(enabled=enabled, **kwargs)
    return _debugger

def reset_debugger():
    """Reset global debugger"""
    global _debugger
    _debugger = None

