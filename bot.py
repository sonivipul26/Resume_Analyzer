import os
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Import local modules
from parsers import parse_resume
from ai_engine import evaluate_resume, optimize_resume
from pdf_generator import generate_pdf_from_json

# Load environment variables
load_dotenv()

# States for ConversationHandler
WAITING_FOR_JD, WAITING_FOR_RESUME = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Send a message when the command /start is issued."""
    await update.message.reply_text(
        "👋 Welcome to the **Resume Analyzer Bot**!\n\n"
        "Let's see if you are a match for your dream job.\n"
        "Please send me the **Job Description (JD)** as a text message.",
        parse_mode="Markdown"
    )
    return WAITING_FOR_JD

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Process cancelled. Send /start to begin again.")
    context.user_data.clear()
    return ConversationHandler.END

async def receive_jd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the JD and asks for the resume."""
    jd_text = update.message.text
    if not jd_text:
        await update.message.reply_text("Please send the Job Description as text.")
        return WAITING_FOR_JD
    
    context.user_data['jd_text'] = jd_text
    await update.message.reply_text("Great! Now, please upload your **Resume** (PDF or DOCX).", parse_mode="Markdown")
    return WAITING_FOR_RESUME

async def receive_resume(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Downloads the resume, parses it, and runs the AI Engine."""
    document = update.message.document
    
    if not document:
        await update.message.reply_text("Please upload a file (PDF or DOCX).")
        return WAITING_FOR_RESUME
    
    file_name = document.file_name
    ext = os.path.splitext(file_name)[1].lower()
    
    if ext not in [".pdf", ".docx", ".doc"]:
        await update.message.reply_text("Unsupported file format. Please upload a PDF or DOCX.")
        return WAITING_FOR_RESUME
    
    processing_msg = await update.message.reply_text("⏳ Downloading your resume...")
    
    try:
        # Download file
        file = await context.bot.get_file(document.file_id)
        file_path = f"temp_{update.message.from_user.id}_{file_name}"
        await file.download_to_drive(file_path)
        
        await processing_msg.edit_text("⏳ Parsing document...")
        resume_text = parse_resume(file_path)
        
        # Clean up temp file
        if os.path.exists(file_path):
            os.remove(file_path)
            
        if not resume_text:
            await processing_msg.edit_text("❌ Failed to extract text from the document. Please try a different file.")
            return ConversationHandler.END
            
        jd_text = context.user_data['jd_text']
        
        await processing_msg.edit_text("🤖 AI is evaluating your resume against the JD...")
        
        # Run AI Evaluation
        evaluation = evaluate_resume(jd_text, resume_text)
        
        if "error" in evaluation:
            await processing_msg.edit_text("❌ Error during evaluation. Please verify your GEMINI_API_KEY.")
            return ConversationHandler.END
        
        # Format the result message
        score = evaluation.get("score", 0)
        result = evaluation.get("result", "FAIL")
        missing_kw = ", ".join(evaluation.get("missing_keywords", []))
        suggestions = "\n- ".join(evaluation.get("suggestions", []))
        
        result_msg = (
            f"📊 **Match Score**: {score}/10.0\n"
            f"🎯 **Result**: {result}\n\n"
            f"🔍 **Missing Keywords**: {missing_kw if missing_kw else 'None'}\n\n"
            f"💡 **Improvement Suggestions**:\n- {suggestions}"
        )
        
        await processing_msg.edit_text(result_msg, parse_mode="Markdown")
        
        # Generate optimized resume
        optimizing_msg = await update.message.reply_text("✨ Generating an ATS-Optimized version of your resume...")
        
        optimized_data = optimize_resume(jd_text, resume_text)
        
        if "error" in optimized_data:
            await optimizing_msg.edit_text("❌ Error during optimization.")
            return ConversationHandler.END
            
        layouts = {
            "Single Column": "single_column.html",
            "Two Column": "two_column.html",
            "Compact": "compact.html"
        }
        
        await optimizing_msg.delete()
        
        for layout_name, template_file in layouts.items():
            pdf_path = f"optimized_{layout_name.replace(' ', '_')}_{update.message.from_user.id}.pdf"
            pdf_generated_path = generate_pdf_from_json(optimized_data, pdf_path, template_name=template_file)
            
            if pdf_generated_path and os.path.exists(pdf_generated_path):
                # Send file
                with open(pdf_generated_path, 'rb') as f:
                    await update.message.reply_document(
                        document=f, 
                        filename=f"Optimized_{layout_name.replace(' ', '_')}.pdf",
                        caption=f"📄 {layout_name} Layout"
                    )
                os.remove(pdf_generated_path)
            else:
                await update.message.reply_text(f"❌ Failed to generate the {layout_name} PDF.")
            
    except Exception as e:
        await processing_msg.edit_text(f"❌ An error occurred: {str(e)}")
        
    context.user_data.clear()
    return ConversationHandler.END

def main() -> None:
    """Start the bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("Error: TELEGRAM_BOT_TOKEN is not set in .env")
        return

    application = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_JD: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_jd)],
            WAITING_FOR_RESUME: [MessageHandler(filters.Document.ALL, receive_resume)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)

    print("🤖 Resume Analyzer Bot is running...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
