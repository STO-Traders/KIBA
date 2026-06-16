package com.stotraders.kiba

import com.intellij.execution.configurations.GeneralCommandLine
import com.intellij.execution.util.ExecUtil
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.progress.ProgressIndicator
import com.intellij.openapi.progress.Task
import com.intellij.openapi.project.Project
import com.intellij.openapi.ui.Messages

/** Drives the KIBA agent from JetBrains IDEs via headless mode (`kiba -p ...`). */
object Kiba {
    private fun binary(): String = System.getenv("KIBA_BIN") ?: "kiba"

    fun run(project: Project?, prompt: String, autonomous: Boolean) {
        object : Task.Backgroundable(project, "KIBA thinking…", true) {
            override fun run(indicator: ProgressIndicator) {
                val cmd = GeneralCommandLine(binary(), "-p", prompt)
                project?.basePath?.let { cmd.setWorkDirectory(it) }
                if (autonomous) {
                    cmd.environment["KIBA_AUTO_APPROVE"] = "1"
                    project?.basePath?.let { cmd.environment["KIBA_TRUSTED_DIRS"] = it }
                }
                val text: String = try {
                    val out = ExecUtil.execAndGetOutput(cmd)
                    out.stdout.ifBlank { out.stderr }.ifBlank { "(no output)" }
                } catch (e: Exception) {
                    "Failed to run KIBA: ${e.message}\n(Set the KIBA_BIN env var or put 'kiba' on PATH.)"
                }
                ApplicationManager.getApplication().invokeLater {
                    Messages.showInfoMessage(project, text, "KIBA")
                }
            }
        }.queue()
    }
}

class KibaAskAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val prompt = Messages.showMultilineInputDialog(e.project, "Ask KIBA:", "KIBA", "", null, null) ?: return
        if (prompt.isBlank()) return
        Kiba.run(e.project, prompt, autonomous = false)
    }
}

class KibaAskSelectionAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        val sel = editor?.selectionModel?.selectedText ?: ""
        val seed = if (sel.isNotBlank()) "About this code:\n```\n$sel\n```\n\n" else ""
        val prompt = Messages.showMultilineInputDialog(e.project, "Ask KIBA about the selection:", "KIBA", seed, null, null) ?: return
        if (prompt.isBlank()) return
        Kiba.run(e.project, prompt, autonomous = false)
    }
}

class KibaRunOnFileAction : AnAction() {
    override fun actionPerformed(e: AnActionEvent) {
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE)
        val target = file?.path ?: "the project"
        val task = Messages.showMultilineInputDialog(e.project, "KIBA — what should it do to $target?", "KIBA", "", null, null) ?: return
        if (task.isBlank()) return
        val full = if (file != null) "$task\n\nTarget file: ${file.path}" else task
        Kiba.run(e.project, full, autonomous = true)
    }
}
