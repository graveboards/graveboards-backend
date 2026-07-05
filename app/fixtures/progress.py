"""Progress bar handler for fixture fetch operations."""


class ProgressBar:
    """Simple progress bar handler for fetch operations."""
    
    def __init__(self, no_progress: bool = False):
        self.no_progress = no_progress
        self._progress = None
        self._task_ids = {}
    
    def start(self):
        """Start the progress display."""
        if self.no_progress:
            return
        try:
            from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
            self._progress = Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                TimeRemainingColumn(),
            )
            self._progress.start()
        except ImportError:
            pass
    
    def update(self, category: str, current: int, total: int):
        """Update progress for a category."""
        if self.no_progress or not self._progress:
            return
        
        try:
            if category not in self._task_ids:
                self._task_ids[category] = self._progress.add_task(
                    f"Fetched {category}", total=total
                )
            
            task_id = self._task_ids[category]
            self._progress.update(task_id, completed=current)
        except Exception:
            pass
    
    def stop(self):
        """Stop the progress display."""
        if self._progress:
            try:
                self._progress.stop()
            except Exception:
                pass
